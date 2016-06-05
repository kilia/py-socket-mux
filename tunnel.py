import time
import sys
import asyncore, socket
import Queue, threading
import struct
from config import log

SIZE = 1
BUF_SIZE = 4096
QUEUE_SIZE = 512

if len(sys.argv) > 1:
    SIZE = int(sys.argv[1])
#print 'multiplex:', SIZE

def fullread(sock, buf, size):
    cur = len(buf)
    if cur < size:
        buf += sock.recv(size - cur)
    return buf

class Tunnel(object):
    def __init__(self, qs = QUEUE_SIZE, emptyloop = 0.001):
        self._wq = Queue.Queue(qs)
        self._rq = Queue.Queue(qs)
        self._el = emptyloop
    
    def send(self, buf):
        #print 'send', buf
        self._wq.put(buf)
        
    def recv(self):
        if self._rq.empty():
            time.sleep(self._el)
            return None
        buf = self._rq.get()
        #print 'recv', buf
        return buf
    
    def pipe_send(self, buf):
        #print 'psend', buf
        self._rq.put(buf)
        
    def pipe_recv(self):
        if self._wq.empty():
            time.sleep(self._el)
            return None
        buf = self._wq.get()
        #print 'precv', buf
        return buf
    
class TunnelServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self._tunnel = Tunnel()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.listen(1)
        self._pipes = []

    def get_tunnel(self):
        return self._tunnel
        
    def close_all(self):
        self.close()
        for p in self._pipes:
            p.close()
        
    def handle_accept(self):
        # when we get a client connection start a dispatcher for that
        # client
        socket, address = self.accept()
        #print 'Connection by', address
        self._pipes.append(Pipe(socket, self._tunnel))

class TunnelClient(object):
    def __init__(self, host, port, mp = 8):
        self._tunnel = Tunnel()
        self._pipes = []
        for i in xrange(mp):
            #print i, Pipe
            p = Pipe(None, self._tunnel)
            self._pipes.append(p)
            p.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            p.connect((host, port))

    def get_tunnel(self):
        return self._tunnel
        
    def close_all(self):
        for p in self._pipes:
            p.close()
        
class Pipe(asyncore.dispatcher):

    def __init__(self, sock, tunnel):
        #print 'pipe init', sock
        asyncore.dispatcher.__init__(self, sock)
        self._tunnel = tunnel
        
        self.reset_read()
        self._writebuf = ''
        
    def reset_read(self):    
        self._header = '' 
        self._buf = ''
        self._size = -1

    def handle_close(self):
        # todo error handling
        self.close()

    def handle_read(self):
        # first fill the header
        self._header = fullread(self, self._header, 4) # header size is only 4 now
        if len(self._header) == 4:
            self._size, = struct.unpack('<i',self._header)
            self._buf = fullread(self, self._buf, self._size) # read in all content
            if len(self._buf) == self._size:
                #print self, 'read', self._buf
                self._tunnel.pipe_send(self._buf)
                self.reset_read()

    def handle_write(self):
        if len(self._writebuf) > 0: # last buffer is still not empty
            sent = self.send(self._writebuf)
            self._writebuf = self._writebuf[sent:]
        if len(self._writebuf) == 0: # buffer is empty, we can fill in more
            #while not self._writeq.empty():
            data = self._tunnel.pipe_recv()
            if not data is None:
                #print self, 'write', data
                self._writebuf += struct.pack('<i',len(data)) + data

'''
Test Suit:
'''

s = TunnelServer('0.0.0.0', 5555)
ts = s.get_tunnel()
c = TunnelClient('localhost',5555,2)
tc = c.get_tunnel() 

s0 = threading.Thread(target=asyncore.loop)
s0.start()

TEST_SIZE = 32
for i in xrange(TEST_SIZE):
    tc.send('%03d hello' % i)
    #time.sleep(0.01)

def test_read(tunnel, test_size, comment = ''):    
    i = 0    
    while i < test_size:
        data = tunnel.recv()
        if not data is None:
            log('%s %s %s' %(comment, 'get', data))
            tunnel.send(data)
            i += 1
            time.sleep(0.1)
    log('%s done' % (comment,))

s1 = threading.Thread(target=test_read, args=(ts, TEST_SIZE, 'server'))
s2 = threading.Thread(target=test_read, args=(tc, TEST_SIZE, 'client'))
s1.start()
s2.start()
s1.join()
s2.join()
#time.sleep(2.0)
s.close_all()
log('server pipes closed')
c.close_all()
log('client pipes closed')

log('all closed')