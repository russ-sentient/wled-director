from wldirector.wldirector import WDirector

## MAIN STARTUP
if __name__ == '__main__':
    import time
    director = WDirector()

    while( True ):
        director.Update()
        
        time.sleep( 1 )