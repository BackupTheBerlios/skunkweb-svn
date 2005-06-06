"""

contains utility functions for obtaining configuration data for the pydo tests --
either from command line or a config file

"""

import optparse
import os
import traceback
from pydo.dbi import initAlias, _driverConfig

DEFAULT_CONFIG='~/.pydotestrc'

def _readConfigFile(fname=DEFAULT_CONFIG):
    fname=os.path.expanduser(fname)
    d={}
    if os.path.exists(fname):
        execfile(fname, {}, d)
    return d

def readCmdLine(args, usage=None):
    if usage:
        parser=optparse.OptionParser(usage=usage)
    else:
        parser=optparse.OptionParser()
    parser.add_option('-c', '--config',
                      dest='config',
                      help='config file to read (default: ~/.pydotestrc)',
                      default='~/.pydotestrc',
                      metavar='CONFIG',
                      action='store')
    parser.add_option('-d', '--drivers',
                      dest='drivers',
                      help='drivers to test against',
                      metavar='DRIVERS',
                      action='store')
    parser.add_option('-t', '--tags',
                      dest='tags',
                      help='tags to use',
                      metavar='TAGS',
                      action='store')
    parser.add_option('-v', '--verbose',
                      dest='verbose',
                      help="whether to be verbose",
                      action='store_true',
                      default=None)
    opts, args=parser.parse_args(args)
    try:
        c=_readConfigFile(opts.config)
    except:
        traceback.print_exc()
        parser.error("error reading config file!")

    if not opts.tags:
        tags=set()
    else:
        tags=set(opts.tags.split())
    possdrivers=set(_driverConfig)        
    if not opts.drivers:
        drivers=possdrivers
    else:
        drivers=set(opts.drivers.split())
        if not drivers.issubset(possdrivers):
            parser.error("unrecognized driver(s): %s" % ', '.join(drivers.difference(possdrivers)))

    retdrivers={}
    # init all the aliases
    for d in drivers:
        try:
            connectArgs=c[d]
        except:
            parser.error("no config for driver: %s" % d)
        else:
            connectArgs['driver']=d
            if opts.verbose is not None:
                connectArgs['verbose']=opts.verbose
            # the connection alias will always be "pydotest"
            connectArgs['alias']='pydotest'
            if not isinstance(connectArgs, dict):
                parser.error("configuration error: must be a dict, got a %s" % type(connectArgs))
            retdrivers[d]=connectArgs

    return retdrivers, tags
