
from wldirector.config import models
from time import sleep

## debug our new data handlers
def trace_object( obj, indent = 0 ) -> None:
    if isinstance( obj, dict ):
        for key, value in obj.items():
            print( " "*indent, f'{key}:' )
            trace_object( value, indent+2 )
    elif isinstance( obj, list ):
        for value in obj:
            trace_object( value, indent+2 )
    elif isinstance( obj, models.WLDBaseModel ):
        print( " "*indent, obj.get() )
    else:
        print( " "*indent, obj )



if __name__ == "__main__":
    config = WLDConfig( "test" )

    while True:
        print( "=========================================" )
        data = config.load()
        print( "=========================================")
        trace_object( data )
        sleep( 5.0 )


from wldirector.config.handler import WLDConfig