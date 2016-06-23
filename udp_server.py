import struct, time
from collections import deque

from gevent.server import DatagramServer
from gevent import queue
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
        if count > 64: count = 64
        if count < 1: count = 1
        for i in xrange(count):
            data = struct.pack('<i', self._seq) + self._payload
            self._seq += 1
            #self.socket.sendto(data, address)
            q.put((self.socket, data, address))


def sender(limit = 8 * 1024 * 1024):
    global q
    print 'sender started'
    window_size = 128
    window = deque(maxlen = window_size)
    t = time.time()
    for _ in xrange(window_size):
        window.append((t, 0))
    bytes_in_window = 0
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

        # check if we need to slow down
        dt = t - oldest[1]
        sleeptime = bytes_in_window*1.0/limit - dt
        if sleeptime > 0:
            gevent.sleep(sleeptime)

if __name__ == '__main__':
    print('Receiving datagrams on :9000')
    gevent.spawn(sender)
    EchoServer('0.0.0.0:9000').serve_forever()
