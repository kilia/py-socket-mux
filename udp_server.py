import struct
from gevent.server import DatagramServer

class EchoServer(DatagramServer):
    def __init__(self, *args, **kwargs):
        self._seq = 0
        self._payload = 'x' * 1024 # default MTU ~ 1400
        DatagramServer.__init__(self, *args, **kwargs)

    def handle(self, data, address):
        assert(len(data)==4)
        count, = struct.unpack('<i', data)
        if count > 64: count = 64
        if count < 1: count = 1
        for i in xrange(count):
            data = struct.pack('<i', self._seq) + self._payload
            self._seq += 1
            self.socket.sendto(data, address)

if __name__ == '__main__':
    print('Receiving datagrams on :9000')
    EchoServer('0.0.0.0:9000').serve_forever()
