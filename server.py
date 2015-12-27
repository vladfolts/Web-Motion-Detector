#!/usr/bin/python

from Queue import Queue
from optparse import OptionParser
from threading  import Thread
import BaseHTTPServer
import os
import SimpleHTTPServer
import ssl
import json

q = Queue()

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.getheader('content-length', 0))
        try:
            j = self.rfile.read(content_len)
            r = json.loads(j)
            for i in r:
                q.put(i)
        except Exception, x:
            print("error: %s" % x)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write('OK')
        return

def run(options):
    port = options.port
    print('serving at port: %d' % port)
    httpd = BaseHTTPServer.HTTPServer(('', port), ServerHandler)

    if options.certfile:
        try:
            httpd.socket = ssl.wrap_socket(httpd.socket, certfile=options.certfile, server_side=True)
        except e:
            print("ssl error: " + e)
            return

    httpd.serve_forever()

def notify(msg):
    if os.name != 'nt':
        print(msg);
        return

    import ctypes
    MessageBox = ctypes.windll.user32.MessageBoxA

    MB_SYSTEMMODAL = 0x1000
    MessageBox(None, msg, 'Warning!', MB_SYSTEMMODAL)

def main(options):
    t = Thread(target=run, args=([options]))
    t.daemon = True # thread dies with the program
    t.start()

    while True:
        i = 0
        try:
            i = q.get(True, 5)
        except Exception:
            notify('no signal detected');

        if i > options.sensitivity:
            notify('Incoming!')

            # clear queue (without analyzing) after notification is shown
            while not q.empty():
                q.get()

parser = OptionParser()
parser.add_option("-p", "--port", default=8000, type=int, dest="port",
                  help="serve at HTTP port [default: %default]")
parser.add_option("-s", "--sensitivity", default=100000, type=int, dest="sensitivity",
                  help="motion sensitivity [default: %default]")
parser.add_option("-c", "--certfile", default=None, dest="certfile",
                  help="use SSL with certificate file (path to .pem)")
(options, args) = parser.parse_args()

main(options)

