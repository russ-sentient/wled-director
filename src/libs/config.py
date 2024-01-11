## TODO: create a YAML class, and helper classes for yaml constructors to handle LISTS, RANDOMS.
## - Try to find a way to pass the parent key to the constructor to use with this ( list can handle category, random can have automatic keys, etc )
from typing import Any

import yaml
from yamlinclude import YamlIncludeConstructor

from .logger import WLDLogger

from .random_daemon import WLDRandomDaemon

import random
import os, pathlib
from datetime import datetime

## config handler class.  cache data at init, only pull from os if modified date is newer than stored
class WLDConfig():
    def __init__(self, config_name:str ) -> None:
        self._config_file   = f"{WLDYaml.CONFIG_DIR}/{config_name}.yaml"
        self._log           = WLDLogger.get( f"WLDConfig({config_name})" )
        self._data          = None
        self._cfg_modified  = datetime.min
        
        self.load()
        
    def load( self ) -> Any:
        modified = datetime.fromtimestamp( pathlib.Path( self._config_file ).stat().st_mtime )
        
        if modified > self._cfg_modified:
            try:
                with open( self._config_file ) as cfg_file:
                    self._data = yaml.load( cfg_file, Loader=WLDYaml.WLDYamlLoader )
            except Exception as e:
                self._log.error( e )
                
        ## we do not want to return a mutable reference to our private data, send a copy
        return ( self._data.copy() if isinstance(self._data, (dict|list)) else self._data )
    
    
            
    def dump( self, data:Any = None ) -> bool:
        try:
            with open( self._config_file, 'w' ) as cfg_file:
                yaml.dump( data=data, stream=cfg_file, default_flow_style=None, Dumper=WLDYaml.WLDYamlDumper )
                return True
        except Exception as e:
            self._log.error( e )
            
        return False
        
## dataclass for YAML !rand_int functionality
## define !rand_int in config, then when it is encountered in parsing pass we call get() method to get the value.
## handle all keyed random info internally.
class WLDRandInt():
    def __init__(self, key:str|None = None, min:int = 0, max:int = 0 ) -> None:
        self._key = f"INT:{key}" if isinstance(key, str ) else None
        self._min = min
        self._max = max

    def get(self) -> int:
        if self._key and self._key in WLDRandomDaemon.keyed_randoms:
            return WLDRandomDaemon.keyed_randoms[self._key]
        else:
            rand = random.randrange(self._min, self._max)
            
            ## store random if we are keyed
            if self._key:
                WLDRandomDaemon.keyed_randoms[self._key] = rand
            return rand 
        
    
## dataclass for YAML !clist functionality
## hold static config for all instances, get lists from its cached data
## should we make a pick function here too?  could simplify other code
class WLDCList():
    _lists = WLDConfig( "lists" )
    _log = WLDLogger.get( "WLDCList()" )  
    
    def __init__(self, name:str ) -> None:
        self._name = name
        
    ## get one item from list ( if index is not defined should we pick at random here? )
    def get( self, list_type:str, index:int|None = None ) -> Any:
        try:
            m_list = WLDCList._lists.load()[list_type]
        except KeyError as e:
            self.log( e )
            return None
        
        if index == None:
            ## TODO: put weighted pick function here...
            
            if isinstance( m_list, list ):
                return random.choice( m_list )
            elif isinstance( m_list, dict ):
                return random.choice( tuple(m_list.keys()) )
            else:
                self.log( "can't pick from non-iterable list, returning None" )
                return None
        else:
            if isinstance( m_list, list ):
                return m_list[index%len(m_list)]
            elif isinstance( m_list, dict ):
                return tuple(m_list.keys())[index%len(m_list)]
            else:
                self.log( "index supplied for non-iterable list, returning None" )
                return None
            
    def log( self, msg:Any, level:str = "error" ) -> None:
        msg = f"[{self._name}] - {msg}"
        
        if level == "error":
            WLDCList._log.error( msg )
        elif level == "debug":
            WLDCList._log.debug( msg )
        elif level == "warning":
            WLDCList._log.warning( msg )
        else:
            WLDCList._log.info( msg )   


class WLDYaml():
    CONFIG_DIR = f"{os.getcwd()}/config"
    
    ## define our loader so we can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlLoader( yaml.SafeLoader ):
        def __init__(self, **kwargs ) -> None:
            super().__init__(**kwargs)

            ## add constructors
            self.add_constructor( "!clist", WLDYaml._clist_constructor )
            self.add_constructor( "!rand_int", WLDYaml._rand_int_constructor )
            
            YamlIncludeConstructor.add_to_loader_class( WLDYaml.WLDYamlLoader, base_dir=WLDYaml.CONFIG_DIR )
        
    ## define constructors:    
    @staticmethod
    def _clist_constructor( loader: WLDYamlLoader, node: yaml.nodes.MappingNode ) -> WLDCList:
        return WLDCList( **loader.construct_mapping(node) ) # type: ignore
    
    @staticmethod
    def _rand_int_constructor( loader: WLDYamlLoader, node: yaml.nodes.MappingNode ) -> WLDRandInt:
        return WLDRandInt( **loader.construct_mapping(node) ) # type: ignore
    
    ## define our dumper so we can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlDumper( yaml.SafeDumper ):
        def __init__(self, **kwargs ) -> None:
            super().__init__(**kwargs)
            
            