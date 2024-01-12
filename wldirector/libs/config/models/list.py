from typing import Any 
from config.handler import WLDConfig 
from logger import WLDLogger  
import random

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
    def get( self, list_type:str, index:int|None = None ) -> Any:
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
            WLDRandList._log.error( msg )
        elif level == "debug":
            WLDRandList._log.debug( msg )
        elif level == "warning":
            WLDRandList._log.warning( msg )
        else:
            WLDRandList._log.info( msg ) 





        