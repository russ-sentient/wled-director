from typing import Any 
from .model import WLDBaseModel 
import random

## FIXME: we should pass all info on initialization and check validity.  take optional param index for static list addressing.  Add a parser to pull a range. 
## TODO: consider using regexp to parse complicated scalars instead of writing messy mapppings.  ie: !list 
        
class WLDRandList(WLDBaseModel):
    _lists = None
    
    def __init__(self, name:str ) -> None:
        if WLDRandList._lists == None:
            WLDRandList._lists = WLDConfig( "lists", load=False )
            
        self._data['name'] = name
        
    ## get one item from list ( if index is not defined should we pick at random here? )
    def get( self, list_type:str, index:int|None = None ) -> Any:
        try:
            m_list = WLDRandList._lists.load()[list_type][self._data['name']]
        except KeyError as e:
            if str(e)[1:-1] == self._data['name']:
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

from ..handler import WLDConfig 