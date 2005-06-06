import sys
import logging

import config
from testingtesting import runNamespace, info, logger
logger.setLevel(logging.INFO)
from pydo import initAlias, delAlias

# import the actual tests

if __name__=='__main__':
    drivers, tags=config.readCmdLine(sys.argv[1:])
    res=0
    for d, connectArgs in drivers.iteritems():
        initAlias(**connectArgs)
        curtags=list(tags)+[d]
        if tags:
            info("testing with driver: %s, tags: %s", d, ", ".join(tags))
        else:
            info("testing with driver: %s", d)
        try:
            res |= runNamespace(curtags)
        finally:
            delAlias('pydotest')
    sys.exit(res)
