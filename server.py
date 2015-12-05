#!/usr/bin/python

from Queue import Queue
import os
import SimpleHTTPServer
import SocketServer
import sys
from threading  import Thread
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
        
        self.wfile.write('OK')
        return

def run(port):
    print('serving at port: %d' % port)
    httpd = SocketServer.TCPServer(("", port), ServerHandler)
    httpd.serve_forever()

def notify(msg):
    if os.name != 'nt':
        print(msg);
        return

    import ctypes
    MessageBox = ctypes.windll.user32.MessageBoxA

    MB_SYSTEMMODAL = 0x1000
    MessageBox(None, msg, 'Warning!', MB_SYSTEMMODAL)

def main(port, sensitivity):
    t = Thread(target=run, args=([port]))
    t.daemon = True # thread dies with the program
    t.start()

    while True:
        i = 0
        try:
            i = q.get(True, 5)
        except Exception:
            notify('no signal detected');

        if i > sensitivity:
            notify('Incoming!')

            # clear queue (without analyzing) after notification is shown
            while not q.empty():
                q.get()

args_num = len(sys.argv)
port = 8000 if args_num < 2 else int(sys.argv[1])
sensitivity = 100000 if args_num < 3 else int(sys.argv[2])

main(port, sensitivity)

