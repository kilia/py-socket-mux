import struct, random
import gevent
from gevent import socket
from gevent.event import Event

from config import log

''' 
client - window - conversation - tunnel ~ tunnel - conversation - window - server
'''

#conversation = None
#tunnel = None
#make_server_connection = None

STAT_NORMAL = ' '
STAT_INIT = 'i'
STAT_CLOSE = 'x'

class Window(object):
    '''
    suppose no packet will be lost, but the order may be chaos.
    deal with the out of order problem with a window algorithm.
    '''
    def __init__(self, sock, conv, cid = None, max_window_size = 100*1024, auto_spawn = False):
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
    
    def get_side(self):
        return self._conv.get_side()
        
    def start(self):
        #if hasattr(self._sock, 'settimeout'):
        #    self._sock.settimeout(0.1)
        seq = 0
        self.send_to_conversation(seq, '') # send a '' packet to init the connection to the sever
        seq += 1
        while True:
            try:
                data = self._sock.recv(1024) 
                #print self._sock, '#', self._cid, 'recv:', len(data), 'bytes'
                if len(data) == 0:
                    raise Exception('connection closed')
                self.send_to_conversation(seq, data)
            except Exception as err:
                print err, type(err), 'cid#', self._cid, 'shutdown soon'
                gevent.sleep(1.0)
                self.close()
                return # exit
            seq += 1
    
    def close(self): # on disconnect/reset/other exceptions close up
        self._sock.close()
        self._conv.unregister(self, self._cid)
        
    def send_to_conversation(self, seq, data): # send data to conversation
        #print self.get_side(), self._cid, 'send to conversation #seq=', seq, 'size=', len(data) 
        self._conv.send_to_tunnel(self._cid, struct.pack('<i',seq) + data)
        
    def send_to_socket(self, data): # recv data from conversation :->
        assert(len(data) >= 4)
        seq, = struct.unpack('<i',data[:4])
        #print self.get_side(), self._cid, 'seq#', seq, '_ri', self._ri
        assert(0 <= (seq - self._ri) <= self._mws) # reorder the sequence
        # TODO what if seq is dupe or too fast? we need to drop it here
        self._rbuffer[seq] = data[4:]
        while self._ri in self._rbuffer:
            try:
                self._sock.sendall(self._rbuffer[self._ri])
            except Exception as err:
                print err, type(err), 'cid#', self._cid, 'shutdown soon'
                gevent.sleep(1.0)
                return
            del self._rbuffer[self._ri]
            self._ri += 1

ColsedWindow = 'closed window'

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
        
    def get_side(self):
        return self._side
        
    def register(self, window, cid = None):
        if not cid:
            cid = random.getrandbits(64)
        self._regd[cid] = window
        print self._side, 'register conversation', cid, 'success'
        return cid
        
    def unregister(self, window, cid):
        assert window == self._regd[cid]
        self._regd[cid] = ColsedWindow # TODO close the window on the other side
        print self._side, 'unregister conversation', cid
        
    def send_to_tunnel(self, cid, data):
        self._tunnel.send_out(struct.pack('<Q',cid) + data)
        
    def send_to_window(self, data):
        assert(len(data)>=8)
        #print self.get_side(), 'dump regd:', self._regd
        cid, = struct.unpack('<Q',data[:8])
        if cid not in self._regd:
            assert(self._side == 'server')
            e = Event()
            self._regd[cid] = e # wait for me 
            w = Window(self._make_server_connection(), self, cid)
            gevent.spawn(w.start)
            self._regd[cid] = w
            e.set() # ready, good to go
        w = self._regd[cid]
        while type(w) == Event:
            w.wait()
            w = self._regd[cid]
        if w == ColsedWindow:
            print self._side, '#', cid, 'already closed, drop packet'
            return
        w.send_to_socket(data[8:])

def donot_make_connection():
    raise NotImplementedError('client side should not make new connection, something must go wrong')

class Tunnel(object): # simple setup: 1 tunnel : 1 conversation : n window(cid)
    '''
    Tunnel manager
    TODO did not deal with tunnel connection lost :(
    '''
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
