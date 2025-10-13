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


class WLDLogger:
    @staticmethod
    def get( name:str ) -> logging.Logger:
        def fmt_filter( record ):
            record.levelname = '<%s>' % record.levelname
            record.funcName = '%s()' % record.funcName
            return True
        
        logger = logging.Logger( name )
        logger.setLevel( logging.DEBUG )
        logger.addFilter( fmt_filter )
        
        STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
        SYSLOG_HANDLER = logging.handlers.SysLogHandler(address = ('graylog-6.knet',1516))
        
        STREAM_FORMATTER = logging.Formatter( f'{logColorCodes.blue}[%(asctime)s] {logColorCodes.light_blue}%(levelname)-8s {logColorCodes.purple}%(filename)s{logColorCodes.reset} {logColorCodes.green}%(name)s{logColorCodes.reset}.{logColorCodes.yellow}%(funcName)s{logColorCodes.reset} %(message)s' ) #, "%Y-%m-%d %H:%M:%S" )
        FILE_FORMATTER = logging.Formatter( f'[%(asctime)s] %(levelname)-8s %(filename)s %(name)s.%(funcName)s %(message)s' ) #, "%Y-%m-%d %H:%M:%S" )

        SYSLOG_HANDLER.setLevel( logging.WARNING )
        SYSLOG_HANDLER.setFormatter( FILE_FORMATTER )
        STDOUT_HANDLER.setLevel( logging.DEBUG )
        STDOUT_HANDLER.setFormatter( STREAM_FORMATTER )
        
        logger.addHandler( STDOUT_HANDLER )
        logger.addHandler( SYSLOG_HANDLER )
        return logger
        
    @staticmethod
    def log_handle_exception( exc_type, exc_value, exc_traceback ) -> None:
        WLDLogger._log.error( "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback) )

    _log = get("WLDLogger")
    sys.excepthook = log_handle_exception  

    

    
    
