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

CONFIG_DIR = f"{os.getcwd()}/config"

## config handler class.  cache data at init, only pull from os if modified date is newer than stored
class WLDConfig():
    def __init__(self, config_name:str, load:bool=True ) -> None:
        self._config_file   = f"{CONFIG_DIR}/{config_name}.yaml"
        self._log           = WLDLogger.get( f"WLDConfig({config_name})" )
        self._data          = None
        self._cfg_modified  = datetime.min

        if load:
            self.load()
        
    def load( self ) -> Any:
        modified = datetime.fromtimestamp( pathlib.Path( self._config_file ).stat().st_mtime )
        
        if modified > self._cfg_modified:
            try:
                with open( self._config_file ) as cfg_file:
                    self._log.debug( "Caching .yaml" )
                    self._data = yaml.load( cfg_file, Loader=WLDYaml.WLDYamlLoader )
                    self._cfg_modified = modified
            except Exception as e:
                self._log.error( e )
                
        ## we do not want to return a mutable reference to our private data, send a copy
        self._log.debug( "Loading from cache" )
        return ( self._data.copy() if isinstance(self._data, (dict|list)) else self._data )
    
    
            
    def dump( self, data:Any = None ) -> bool:
        try:
            with open( self._config_file, 'w' ) as cfg_file:
                yaml.dump( data=data, stream=cfg_file, default_flow_style=None, Dumper=WLDYaml.WLDYamlDumper )
                return True
        except Exception as e:
            self._log.error( e )
            
        return False
    
## TODO: we should write a base WLDModel class so we can call get generically from parse function.
        
## dataclass for YAML !rand_int functionality
## define !rand_int in config, then when it is encountered in parsing pass we call get() method to get the value.
## handle all keyed random info internally.
class WLDRandInt():
    def __init__(self, key:str|None = None, min:int = 0, max:int = 1 ) -> None:
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
        
## FIXME: we should pass all info on initialization and check validity.  take optional param index for static list addressing.  Add a parser to pull a range. 
## TODO: consider using regexp to parse complicated scalars instead of writing messy mapppings.  ie: !list 
        
class WLDRandList():
    _lists = WLDConfig( "lists", load=False )
    _log = WLDLogger.get( "WLDCList()" )  
    
    def __init__(self, name:str ) -> None:
        self._name = name
        
    ## get one item from list ( if index is not defined should we pick at random here? )
    def get( self, list_type:str, index:int|None|WLDRandInt = None ) -> Any:
        try:
            m_list = WLDRandList._lists.load()[list_type][self._name]
        except KeyError as e:
            if str(e)[1:-1] == self._name:
                self.log( f"list {e} not in lists.{list_type}" )
            else:
                self.log( f"list type {e} not found in lists" )
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
            if isinstance( index, WLDRandInt ):
                idx = index.get()
            else:
                idx = index

            if isinstance( m_list, list ):
                return m_list[idx%len(m_list)]
            elif isinstance( m_list, dict ):
                return tuple(m_list.keys())[idx%len(m_list)]
            else:
                self.log( "index supplied for non-iterable list, returning None" )
                return None
            
            
    def log( self, msg:Any, level:str = "error" ) -> None:
        msg = f"[{self._name}] - {msg}"
        
        if level == "error":
            WLDRandList._log.error( msg )
        elif level == "debug":
            WLDRandList._log.debug( msg )
        elif level == "warning":
            WLDRandList._log.warning( msg )
        else:
            WLDRandList._log.info( msg ) 

## replace weighted pick with this?  same as list but we define the weighted choices after the !pick tag
class WLDPick():
    def __init__(self) -> None:
        pass

## random hue ( with offset? )
class WLDRandHue():
    def __init__(self) -> None:
        pass

## manual hue
class WLDHue():
    def __init__(self) -> None:
        pass

## tag to copy another host/groups data
## TODO: pass list of keys from parse function to pull same data from GET()
class WLDCopy():
    ## pass this in when we init director:
    _hosts = None
    ## pass this in as we parse a preset:
    _groups = None

    def __init__(self) -> None:
        pass

class WLDYaml():
    ## define our loader so we can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlLoader( yaml.SafeLoader ):
        def __init__(self, stream ) -> None:
            super().__init__(stream)

            ## add constructors
            self.add_constructor( "!rand_list", WLDYaml._rand_list_constructor )
            self.add_constructor( "!rand_int", WLDYaml._rand_int_constructor )
            
            YamlIncludeConstructor.add_to_loader_class( WLDYaml.WLDYamlLoader, base_dir=CONFIG_DIR )
        
    ## define constructors:    
    @staticmethod
    def _rand_list_constructor( loader: WLDYamlLoader, node: yaml.nodes.ScalarNode ) -> WLDRandList:
        return WLDRandList( name=node.value )
    
    @staticmethod
    def _rand_int_constructor( loader: WLDYamlLoader, node: yaml.nodes.Node ) -> WLDRandInt|None:
        if isinstance( node, yaml.nodes.MappingNode ):
            return WLDRandInt( **loader.construct_mapping(node) ) # type: ignore
        elif isinstance( node, yaml.nodes.ScalarNode ):
            value = node.value
            if str(value).isdigit():
                return WLDRandInt( max=int(value) )
            else:
                return WLDRandInt( key=str(value) )
        elif isinstance( node, yaml.nodes.SequenceNode ):
            return WLDRandInt( key=str(node.value[0].value), min=int(node.value[1].value), max=int(node.value[2].value) )
        
        print( f"!rand_int constructor - error parsing node {node.start_mark}" )
    
    ## define our dumper so we can over-ride __init__ to automatically add our constructors etc.
    class WLDYamlDumper( yaml.SafeDumper ):
        def __init__(self, **kwargs ) -> None:
            super().__init__(**kwargs)
            
            