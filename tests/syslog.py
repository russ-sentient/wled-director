import logging, sys
import logging.handlers

log = logging.getLogger('MyLogger')
log.setLevel(logging.DEBUG)

handler = logging.handlers.SysLogHandler(address = ('graylog.knet',1550))
handler.setLevel( logging.WARNING )
log.addHandler(handler)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel( logging.DEBUG )
log.addHandler(handler)

log.debug('this is debug')
log.critical('this is critical')