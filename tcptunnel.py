import struct, random
import gevent
from gevent import socket

from config import log

''' 
client - window - conversation - tunnel ~ tunnel - conversation - window - server
'''

conversation = None
tunnel = None

class Window(object):
    '''
    suppose no packet will be lost, but the order may be chaos.
    deal with the out of order problem with a window algorithm.
    '''
    def __init__(self, sock, conversation, max_window_size = 256):
        #assert(sock is not None)
        self._sock = sock
        self._ri = 0 # ri ~ receive window index
        self._rbuffer = {} # receive window buffer
        self._conv = conversation
        self._mws = max_window_size
        
    def start(self):
        # register self to conversation
        cid = self._conv.register(self)
        seq = 0
        self.send_to_conversation(seq, '') # send a '' packet to init the connection to the sever
        while True:
            seq += 1
            data = self._sock.recv()
            self.send_to_conversation(cid, seq, data)
        
    def send_to_conversation(self, cid, seq, data): # send data to conversation 
        self._conv.send_to_tunnel(cid, struct.pack('<i',seq) + data)
        
    def send_to_socket(self, data): # recv data from conversation :->
        assert(len(data) > 4)
        seq, = struct.unpack('<i',data[:4])
        
        if 0 <= (seq - self._ri) <= self._mws: # reorder the sequence
            payload = buf[4:]
            self._rbuffer[sid] = data
        while self._ri in self._rbuffer:
            self._sock.sendall(self._rbuffer[self._ri])
            del self._rbuffer[self._ri]
            self._ri += 1        

class Coversation(object):
    def __init__(self, side):
        self._regd = {}
        self._side = side
        
    def register(self, window):
        cid = random.getrandbits(64)
        self._regd[cid] = window
        return cid
        
    def send_to_tunnel(self, cid, data):
        tunnel.send_out(struct.pack('<Q',cid) + data)
        
    def send_to_window(self, data):
        assert(len(data)>8)
        cid, = struct.unpack('<Q',data[:8])
        if cid not in self._regd:
            pass
        self._regd[cid].send_to_socket(data[8:])
        
class Tunnel(object):
    def __init__(self):
        self._tunnels = []
        
    def add_tunnel(self, tunnel):
        self._tunnels.append(tunnel)
    
    def send_out(self, data):
        random.choice(self._tunnels).sendall(data)
    
class TcpTunnel(object):
    def __init__(self, sock):
        self._sock = sock
        
    def send_out(self, data):
        self._sock.sendall(data)
        
    def send_to_conversation(self):
        while True:
            data = self._sock.recv(1024)
            conversation.send_to_window(data)
            

#### test code

def listen():
    server = socket.socket()
    server.bind(('0.0.0.0', 500))
    print server, 'bind'
    server.listen(500)
    while True:
        sock, addr = server.accept()
        print addr, 'connected'
        t = TcpTunnel(sock)
        gevent.spawn(t.send_to_conversation)

def client():
    c = socket.socket()
    c.connect(('127.0.0.1',500))
    while True:
        gevent.sleep(0.1)
        c.sendall('hello world!')


conversation = Coversation('server')
print 'spawn server'        
s = gevent.spawn(listen)
s.start()
c = gevent.spawn(client)
c.start()

s.join()
c.join()


