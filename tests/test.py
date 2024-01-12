from libs.config import *

## debug our new data handlers
def trace_object( obj, indent = 0 ) -> None:
    if isinstance( obj, dict ):
        for key, value in obj.items():
            print( " "*indent, f'{key}:' )
            trace_object( value, indent+2 )
    elif isinstance( obj, list ):
        for value in obj:
            trace_object( value, indent+2 )
    elif isinstance( obj, WLDRandInt ):
        print( " "*indent, obj.get() )
    elif isinstance( obj, WLDRandList ):
        print( " "*indent, obj.get( 'colors' ) )
    else:
        print( " "*indent, obj )



if __name__ == "__main__":
    config = WLDConfig( "test" )
    
    data = config.load()

    trace_object( data )



    