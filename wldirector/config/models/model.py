# template and derive all model classes from this.
# include our logging method here.
from typing import Any
from wldirector.helpers.logger import WLDLogger  

class WLDBaseModel():
    def __init__(self) -> None:
        self._log = WLDLogger.get( self.__class__.__name__ )
        self._data = {}
        
    ## overridden by derived classes.  allows us to call get on any model without needing to test for each instance...
    def get( self ) -> Any:
        pass
    
    def log( self, msg:Any, level:str = "error" ) -> None:
        msg = f"{{{self._data}}} - {msg}"
        
        if level == "error":
            self._log.error( msg )
        elif level == "debug":
            self._log.debug( msg )
        elif level == "warning":
            self._log.warning( msg )
        else:
            self._log.info( msg ) 
    