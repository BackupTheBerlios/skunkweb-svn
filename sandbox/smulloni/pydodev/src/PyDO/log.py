import logging

logger=logging.Logger('PyDO')
debug=logger.debug
error=logger.error
warn=logger.warn
critical=logger.critical
exception=logger.exception
info=logger.info

__all__=['debug', 'error', 'warn', 'critical', 'exception', 'info']
