import struct, time
from collections import deque

from gevent.server import DatagramServer
from gevent import queue, socket
import gevent

q = queue.Queue()

class EchoServer(DatagramServer):
    def __init__(self, *args, **kwargs):
        self._seq = 0
        self._payload = 'x' * 1024 # default MTU ~ 1400
        DatagramServer.__init__(self, *args, **kwargs)

    def handle(self, data, address):
        global q
        assert(len(data)==4)
        count, = struct.unpack('<i', data)
        #if count > 64: count = 64
        #if count < 1: count = 1
        #gevent.sleep(0.5)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1024*1024*10)
        print('buffer:%d\n'%self.socket.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))

        seq = 0
        print 'sending %d packets' % count
        for i in xrange(count):
            data = struct.pack('<i', seq) + self._payload
            seq += 1
            #self.socket.sendto(data, address)
            q.put((self.socket, data, address))

def active_sleep(t):
    assert(t>=0)
    t0 = time.time() + t
    while time.time() < t0:
        gevent.sleep(0)
        pass

def sender(limit = 5 * 1024 * 1024):
    global q
    print 'sender started'
    window_size = 512
    window = deque(maxlen = window_size * 2)
    t = time.time()
    for _ in xrange(window_size):
        window.append((t, 0))
    bytes_in_window = 0
    comp_t = 0
    while True:
        # send a packet
        socket, data, addr = q.get()
        socket.sendto(data, addr)
        
        # append and pop to maintein the moving window
        t = time.time()
        oldest = window.popleft()
        bytes_in_window -= oldest[1]
        bytes_in_window += len(data)
        window.append((t, len(data)))

        if len(window) != window_size:
            print 'window size = %d' % len(window)

        #print bytes_in_window

        # check if we need to slow down
        dt = t - oldest[0]
        #print dt
        sleeptime = bytes_in_window*1.0/limit - dt

        '''
        if sleeptime < comp_t:
            comp_t -= sleeptime
            sleeptime = 0
        else:
            sleeptime -= comp_t
            comp_t = 0            
        '''
        if sleeptime > 0:
            t = time.time()
            #gevent.sleep(sleeptime)
            active_sleep(sleeptime)
            rt = time.time() - t
            comp_t += (rt - sleeptime)/25
            if rt - sleeptime > 0.01:
                print 'want to sleep %.4f sec, acctually %.4f sec' % (sleeptime, rt)

if __name__ == '__main__':
    print('Receiving datagrams on :9000')
    gevent.spawn(sender)
    EchoServer('0.0.0.0:9000').serve_forever()
