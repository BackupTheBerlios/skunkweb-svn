#! /usr/bin/env python

SWEBSITE_URL_BASE='http://www.skunk.org'
WGET='/usr/bin/wget'


import commands
import urllib
import os
def sync(page):
    url='%s%s' % (SWEBSITE_URL_BASE, page)
    tmpfile=os.tmpnam()
    urllib.urlretrieve(url, tmpfile)
    status, output = commands.getstatusoutput('scp %s smulloni@skunkweb.sourceforge.net:~/skunkweb/htdocs%s' % (tmpfile, page))
    print output
    return status


if __name__=='__main__':
    import sys
    args=sys.argv[1:]
    if args:
        for f in args:
            sync(f)
    
