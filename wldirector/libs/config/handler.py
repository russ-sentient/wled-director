## TODO: create a YAML class, and helper classes for yaml constructors to handle LISTS, RANDOMS.
## - Try to find a way to pass the parent key to the constructor to use with this ( list can handle category, random can have automatic keys, etc )
from typing import Any
import yaml
from logger import WLDLogger
import os, pathlib
from datetime import datetime
from config.yaml import WLDYaml

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
        

