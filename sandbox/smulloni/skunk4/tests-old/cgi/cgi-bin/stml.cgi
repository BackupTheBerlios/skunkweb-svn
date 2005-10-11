#! /usr/bin/env python
# -*-python-*-

import os
import sys
import cgitb
cgitb.enable()
import logging
logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig()

sys.path.append('../../src')

import skunk.templating.stml as S
from skunk.components import CompileCache, StringOutputFileComponent
from skunk.cache import DiskCache
import skunk.vfs as V
from skunk.web import HTTPConnection, get_status_line
from stoat.web.adapters.cgiAdapter import CGIAdapter

config={'compileCache' : '/tmp/cgi-compile-cache',
        'componentCache' : '/tmp/cgi-component-cache',
        'fs' : V.LocalFS(os.path.join(os.path.dirname(__file__), '../docroot'))}
for dir in (config['compileCache'], config['componentCache']):
    if not os.path.exists(dir):
        os.mkdir(dir)
factory=S.getDefaultComponentFactory(compileCache=CompileCache(config['compileCache'], useMemory=False),
                                     componentCache=DiskCache(config['componentCache']),
                                     fs=config['fs'])
factory.componentHandlers['file'].suffixMap['.py']=('string', StringOutputFileComponent)                                     

CONNECTION=HTTPConnection(CGIAdapter(), False)
factory.extra_globals['CONNECTION']=CONNECTION
args=CONNECTION.args
action=args.get('action', 'execute')
if action not in ('execute', 'display'):
    action='execute'
# top-level component found via extra path info

path=CONNECTION.env['PATH_INFO']
if not path:
    path='/index.stml'
# execute and print component
comp=factory.createComponent(path)
#res=comp.getCode()
if action=='execute':
    CONNECTION.contentType='text/html'
    res=comp()    
else:
    res=comp.getCode()
    CONNECTION.contentType='text/plain'
CONNECTION.responseBody=res    
CONNECTION.commit()

    
