import logging, sys
import logging.handlers

class logColorCodes:
    grey = "\x1b[38;21m"
    green = "\x1b[1;32m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    purple = "\x1b[1;35m"
    reset = "\x1b[0m"


class WDLogger:

    @staticmethod
    def fmt_filter( record ):
        record.levelname = '<%s>' % record.levelname
        record.funcName = '%s()' % record.funcName
        return True
    
    STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
    SYSLOG_HANDLER = logging.handlers.SysLogHandler(address = ('graylog.knet',1550))
    
    STREAM_FORMATTER = logging.Formatter( f'{logColorCodes.blue}[%(asctime)s] {logColorCodes.light_blue}%(levelname)-8s {logColorCodes.purple}%(filename)s{logColorCodes.reset} {logColorCodes.green}%(name)s{logColorCodes.reset}.{logColorCodes.yellow}%(funcName)s{logColorCodes.reset} %(message)s' ) #, "%Y-%m-%d %H:%M:%S" )
    FILE_FORMATTER = logging.Formatter( f'[%(asctime)s] %(levelname)-8s %(filename)s %(name)s.%(funcName)s %(message)s' ) #, "%Y-%m-%d %H:%M:%S" )


    def __init__(self) -> None:
        WDLogger.SYSLOG_HANDLER.setLevel( logging.WARNING )
        WDLogger.SYSLOG_HANDLER.setFormatter( WDLogger.FILE_FORMATTER )
        WDLogger.STDOUT_HANDLER.setLevel( logging.DEBUG )
        WDLogger.STDOUT_HANDLER.setFormatter( WDLogger.STREAM_FORMATTER )

        self.log = logging.Logger('WDLogger')
        self.log.setLevel(logging.DEBUG)
        
        self.log.addHandler(WDLogger.SYSLOG_HANDLER)
        self.log.addHandler(WDLogger.SYSLOG_HANDLER)
        self.log.addFilter( WDLogger.fmt_filter )

        sys.excepthook = self.log_handle_exception  

    def getLogger( self, name:str ) -> logging.Logger:
        logger = logging.Logger( name )
        logger.setLevel( logging.DEBUG )
        logger.addFilter( WDLogger.fmt_filter )
        logger.addHandler( WDLogger.STDOUT_HANDLER )
        logger.addHandler( WDLogger.SYSLOG_HANDLER )

        return logger

    def log_handle_exception( self, exc_type, exc_value, exc_traceback ) -> None:
        self.log.error( "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback) )
    
