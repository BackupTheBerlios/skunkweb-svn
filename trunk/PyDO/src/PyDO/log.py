import logging

logger=logging.getLogger('pydo')
debug=logger.debug
error=logger.error
warn=logger.warn
critical=logger.critical
exception=logger.exception
info=logger.info
setLogLevel=logger.setLevel

__all__=['debug',
         'error',
         'warn',
         'critical',
         'exception',
         'info',
         'setLogLevel']
