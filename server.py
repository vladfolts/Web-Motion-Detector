#!/usr/bin/python

from Queue import Queue
from base64 import b64encode
from hashlib import sha1
from optparse import OptionParser
from SimpleHTTPServer import SimpleHTTPRequestHandler
from threading  import Thread
import traceback
import BaseHTTPServer
import os
import json
import struct
import ssl

q = Queue()

class WebSocketHandler(object):
    _ws_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11' #'e47b2610-3ce1-4dd6-9ef0-760a026014eb'
    _opcode_continu = 0x0
    _opcode_text = 0x1
    _opcode_binary = 0x2
    _opcode_close = 0x8
    _opcode_ping = 0x9
    _opcode_pong = 0xa

    def __init__(self, requestHandler, msgHandler):
        self.__request_handler = requestHandler
        self.__msg_handler = msgHandler

    def run(self):
        self.__handshake()
        self.__read_messages()
        self.__close()

    def __handshake(self):
        rh = self.__request_handler
        headers = rh.headers
        key = headers['Sec-WebSocket-Key']
        digest = b64encode(sha1(key + self._ws_GUID).hexdigest().decode('hex'))
        rh.send_response(101, 'Switching Protocols')
        rh.send_header('Upgrade', 'websocket')
        rh.send_header('Connection', 'Upgrade')
        rh.send_header('Sec-WebSocket-Accept', str(digest))
        rh.end_headers()

    def __close(self):
        try:
            self.__send_close()
        except Exception, e:
            self.__request_handler.log_message('ignore exception while closing WebSocket: %s.' % e)

    def __send_close(self):
        msg = bytearray()
        msg.append(0x80 + self._opcode_close)
        msg.append(0x00)
        self.__request_handler.request.send(msg)

    def __read_messages(self):
        try:
            while self.__read_next_message():
                pass
        except Exception, e:
            traceback.print_exc()
            self.__request_handler.log_error("closing WebSocket on exception: %s" % e)

    def __read_next_message(self):
        rfile = self.__request_handler.rfile
        #rfile.read(n) is blocking.
        #it returns however immediately when the socket is closed.
        opcode = ord(rfile.read(1)) & 0x0F
        length = ord(rfile.read(1)) & 0x7F
        if length == 126:
            length = struct.unpack(">H", rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", rfile.read(8))[0]
        masks = [ord(byte) for byte in rfile.read(4)]
        decoded = ""
        for char in rfile.read(length):
            decoded += chr(ord(char) ^ masks[len(decoded) % 4])
        
        return self.__on_message(opcode, decoded)

    def __on_message(self, opcode, decoded):
        if opcode == self._opcode_close:
            return False

        if opcode == self._opcode_ping:
            self.__send_message(self._opcode_pong, message)
        elif opcode == self._opcode_pong:
            pass
        elif (opcode == self._opcode_continu or 
                opcode == self._opcode_text or 
                opcode == self._opcode_binary):
            self.__msg_handler(decoded)
        return True

    def __send_message(self, opcode, message):
        request = self.__request_handler.request
        request.send(chr(0x80 + opcode))
        length = len(message)
        if length <= 125:
            request.send(chr(length))
        elif length >= 126 and length <= 65535:
            request.send(chr(126))
            request.send(struct.pack(">H", length))
        else:
            request.send(chr(127))
            request.send(struct.pack(">Q", length))
        if length > 0:
            request.send(message)

class ServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Upgrade", None) == "websocket":
            WebSocketHandler(self, lambda msg: self.__handle_websocket_message(msg)).run()
            #This handler is in websocket mode now.
            #do_GET only returns after client close or socket error.
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def __handle_websocket_message(self, msg):
        try:
            r = json.loads(msg)
            for i in r:
                q.put(i)
        except Exception, x:
            print("error: %s" % x)

def run(options):
    port = options.port
    print('serving at port: %d' % port)
    httpd = BaseHTTPServer.HTTPServer(('', port), ServerHandler)

    if options.certfile:
        try:
            httpd.socket = ssl.wrap_socket(httpd.socket, certfile=options.certfile, server_side=True)
        except Exception, e:
            print("ssl error: %s" % e)
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

