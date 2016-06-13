import struct, random
import gevent
from gevent import socket

from config import log

''' 
client - window - conversation - tunnel ~ tunnel - conversation - window - server
'''

#conversation = None
#tunnel = None
#make_server_connection = None

class Window(object):
    '''
    suppose no packet will be lost, but the order may be chaos.
    deal with the out of order problem with a window algorithm.
    '''
    def __init__(self, sock, conv, cid = None, max_window_size = 256, auto_spawn = False):
        #assert(sock is not None)
        self._sock = sock
        self._ri = 0 # ri ~ receive window index
        self._rbuffer = {} # receive window buffer
        # register self to conversation
        self._conv = conv
        self._cid = self._conv.register(self, cid)
        self._mws = max_window_size
        if auto_spawn:
            gevent.spawn(self.start)
        
    def start(self):
        seq = 0
        self.send_to_conversation(seq, '') # send a '' packet to init the connection to the sever
        while True:
            seq += 1
            data = self._sock.recv(1024)
            self.send_to_conversation(seq, data)
        
    def send_to_conversation(self, seq, data): # send data to conversation
        #print 'send to conversation', seq, len(data), data 
        self._conv.send_to_tunnel(self._cid, struct.pack('<i',seq) + data)
        
    def send_to_socket(self, data): # recv data from conversation :->
        assert(len(data) >= 4)
        seq, = struct.unpack('<i',data[:4])
        
        if 0 <= (seq - self._ri) <= self._mws: # reorder the sequence
            self._rbuffer[seq] = data[4:]
        while self._ri in self._rbuffer:
            self._sock.sendall(self._rbuffer[self._ri])
            del self._rbuffer[self._ri]
            self._ri += 1

class Conversations(object):
    '''
    Conversations is a conversation manager. 
    Each conversation is identified by a unique conversation id.
    By default, one conversation is mapped to only one tunnel
    '''
    def __init__(self, tunnel, side, make_server_connection): # map to a single tunnel
        self._regd = {}
        self._side = side
        self._make_server_connection = make_server_connection
        self._tunnel = tunnel
        
    def register(self, window, cid = None):
        if not cid:
            cid = random.getrandbits(64)
        self._regd[cid] = window
        print 'regist conversation', cid, 'success'
        return cid
        
    def send_to_tunnel(self, cid, data):
        self._tunnel.send_out(struct.pack('<Q',cid) + data)
        
    def send_to_window(self, data):
        assert(len(data)>=8)
        cid, = struct.unpack('<Q',data[:8])
        if cid not in self._regd:
            assert(self._side == 'server')
            w = Window(self._make_server_connection(), self, cid)
            gevent.spawn(w.start)
        self._regd[cid].send_to_socket(data[8:])

def donot_make_connection():
    raise NotImplementedError('client side should not make new connection, something must go wrong')

class Tunnel(object): # simple setup: 1 tunnel : 1 conversation : n window(cid)
    def __init__(self, side, make_server_connection = donot_make_connection):
        self._tunnels = []
        self._side = side
        self._conversation = Conversations(self, side, make_server_connection)
    
    def get_conversation(self):
        return self._conversation
    
    def add_tunnel(self, tunnel):
        self._tunnels.append(tunnel)
        print self._side, 'new tunnel added, total =', len(self._tunnels)
    
    def add_tcp_tunnel(self, sock):
        t = TcpTunnel(sock, self._conversation)
        self.add_tunnel(t)
        # begin conversation immediately
        gevent.spawn(t.send_to_conversation)
        
    def tcp_listen(self, addr): # as server side
        server_sock = socket.socket()
        server_sock.bind(addr)
        print 'server bind on:', addr
        server_sock.listen(500)
        while True:
            sock, addr = server_sock.accept()
            print addr, 'connected'
            self.add_tcp_tunnel(sock)
            
    def tcp_connect(self, addr, tcp_connection_count = 8): # as client side
        def client():
            client_sock = socket.socket()
            client_sock.connect(addr)
            self.add_tcp_tunnel(client_sock)
        greenlets = []
        print 'connecting to ', addr, ' X', tcp_connection_count
        for _ in xrange(tcp_connection_count):
            greenlets.append(gevent.spawn(client))
        gevent.joinall(greenlets)
        print 'all connected'
        
    def send_out(self, data):
        random.choice(self._tunnels).send_out(data)
    
class TcpTunnel(object): # implies reliable connection
    def __init__(self, sock, conv):
        self._sock = sock
        self._conv = conv
        
    def send_out(self, data):
        self._sock.sendall(struct.pack('<i',len(data)) + data)
    
    def recvall(self, size):
        buf = ''
        while len(buf) < size:
            buf += self._sock.recv(size - len(buf)) # python 2.7.10 already optimized str + operation
        return buf
        
    def send_to_conversation(self):
        while True:
            sizebuf = self.recvall(4)
            size, = struct.unpack('<i', sizebuf)
            data = self.recvall(size)
            self._conv.send_to_window(data)
            
''''
#### test code

class dummy_socket(object):
    def __init__(self, filename):
        self._fd = open(filename, 'wb')
        self._seq = 0
        
    def send(self, data):
        self.sendall(data)
        
    def recv(self, size):
        gevent.sleep(1.0)
        self._seq += 1
        return '%010d' % self._seq
        
    def sendall(self, data):
        #print 'send', len(data), data, [ord(c) for c in data]
        self._fd.write(data)
        self._fd.flush()
        gevent.sleep(0.1)

def server_con():
    return dummy_socket('test.txt')
make_server_connection = server_con

def listen():
    server = socket.socket()
    server.bind(('0.0.0.0', 500))
    print server, 'bind'
    server.listen(500)
    global tunnel
    cs = Conversation('server')
    while True:
        sock, addr = server.accept()
        print addr, 'connected'
        t = TcpTunnel(sock, cs)
        tunnel.add_tunnel(t)
        gevent.spawn(t.send_to_conversation)

def client():
    c = socket.socket()
    c.connect(('127.0.0.1',500))
    t = TcpTunnel(c, Conversation('client'))
    seq = 0
    while True:
        gevent.sleep(0.1)
        msg = struct.pack('<Qi',9999, seq)+'hello world!<%d>\n'%seq
        t.send_out(msg)
        seq += 1
        
#conversation = Coversation('server')
tunnel = Tunnel()
#tunnel.add_tunnel(TcpTunnel(dummy_socket()))
print 'spawn server'        
s = gevent.spawn(listen)
#s.start()
c = gevent.spawn(client)
#c.start()

s.join()
c.join()
'''

