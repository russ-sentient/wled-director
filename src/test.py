from libs.config import *


if __name__ == "__main__":
    import os
    print( os.getcwd() )
    quit()
    config = WLDConfig( "test" )
    
    print( config.load() )