import CGIHTTPServer as C
from BaseHTTPServer import HTTPServer
import os
# execute cgi as current user, for testing
C.nobody=os.getuid()

class handler(C.CGIHTTPRequestHandler):
    cgi_directories=['/cgi-bin']


httpd=HTTPServer(("", 8080), handler)
print "serving at port 8080"
httpd.serve_forever()
