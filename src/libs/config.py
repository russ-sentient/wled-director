## TODO: create a YAML class, and helper classes for yaml constructors to handle LISTS, RANDOMS.
## - Try to find a way to pass the parent key to the constructor to use with this ( list can handle category, random can have automatic keys, etc )
from typing import Any

import yaml
import yaml_include

from .logger import WLDLogger

from .random_daemon import WLDRandomDaemon

import random
import os, pathlib
from datetime import datetime

CONFIG_DIR = f"{os.getcwd()}/config"

## config handler class.  cache data at init, only pull from os if modified date is newer than stored
class WLDConfig():
    def __init__(self, config_name:str, load:bool=True ) -> None:
        self._config_name   = config_name
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
                    self._log.debug( f"({self._config_name}.yaml) - Caching." )
                    self._data = yaml.load( cfg_file, Loader=WLDYaml.WLDYamlLoader )
                    self._cfg_modified = modified
            except Exception as e:
                self._log.error( e )
                
        ## we do not want to return a mutable reference to our private data, send a copy
        self._log.debug( f"({self._config_name}.yaml) - Loading from cache." )
        return ( self._data.copy() if isinstance(self._data, (dict|list)) else self._data )
    
    
            
    def dump( self, data:Any = None ) -> bool:
        try:
            with open( self._config_file, 'w' ) as cfg_file:
                yaml.dump( data=data, stream=cfg_file, default_flow_style=None, Dumper=WLDYaml.WLDYamlDumper )
                return True
        except Exception as e:
            self._log.error( e )
            
        return False
    
class WLDBaseTag():
    _memory = dict()
    # overridden by child classes.  call from program to get the value.

    def get(self,call_hint:str = "" ) -> Any:
        pass

    @classmethod
    def flush_memory( cls ) -> None:
        cls._memory.clear()

    @classmethod
    def hasKey( cls, key ) -> bool:
        return key in cls._memory

    @classmethod
    def getKey( cls, key ) -> Any:
        if key in cls._memory:
            return cls._memory[key]
        else:
            return None
        
    @classmethod
    def setKey( cls, key, value ) -> None:
        if key in cls._memory:
            pass # need error handling here
        else:
            cls._memory[key] = value
        
        
## dataclass for YAML !rand_int functionality
## define !rand_int in config, then when it is encountered in parsing pass we call get() method to get the value.
## handle all keyed random info internally.
class WLDRandInt(WLDBaseTag):
    def __init__(self, key:str|None = None, min:int = 0, max:int = 1 ) -> None:
        self._key = f"INT:{key}" if isinstance(key, str ) else None
        self._min = min
        self._max = max

    def get(self, call_hint:str = '' ) -> int:
        if self._key and self.hasKey( self._key ):
            return self.getKey( self._key )
        
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
        
class WLDRandList(WLDBaseTag):
    _lists = WLDConfig( "lists", load=False )
    _log = WLDLogger.get( "WLDRandList()" )
    
    def __init__(self, name:str ) -> None:
        self._name = name
        
    ## get one item from list ( if index is not defined should we pick at random here? )
    def get( self, list_type:str = '' ) -> Any:
        try:
            m_list = WLDRandList._lists.load()[list_type][self._name]
        except KeyError as e:
            if str(e)[1:-1] == self._name:
                self.log( f"list {e} not in lists.{list_type}" )
            else:
                self.log( f"list type {e} not found in lists" )
            return None
        
        ## TODO: put weighted pick function here...
            
        if isinstance( m_list, list ):
            return random.choice( m_list )
        elif isinstance( m_list, dict ):
            return random.choice( tuple(m_list.keys()) )
        else:
            self.log( "can't pick from non-iterable list, returning None" )
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
class WLDPick(WLDBaseTag):
    def __init__(self) -> None:
        pass

## random hue ( with offset? )
class WLDRandHue(WLDBaseTag):
    def __init__(self) -> None:
        pass

## manual hue
class WLDHue(WLDBaseTag):
    def __init__(self) -> None:
        pass

## tag to copy another host/groups data
## TODO: pass list of keys from parse function to pull same data from GET()
class WLDCopy(WLDBaseTag):
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
            self.add_constructor("!include", yaml_include.Constructor(base_dir='./config'))
        
    ## define constructors:    
    @staticmethod
    def _rand_list_constructor( loader: WLDYamlLoader, node: yaml.nodes.Node ) -> WLDRandList:
        if isinstance( node, yaml.nodes.MappingNode ):
            return WLDRandList( **loader.construct_mapping(node) ) #type: ignore
        elif isinstance( node, yaml.nodes.ScalarNode ):
            if isinstance( node.value, str ):
                return WLDRandList( node.value )
        elif isinstance( node, yaml.nodes.SequenceNode ):
            return WLDRandList( node.value[0] )
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
            
            