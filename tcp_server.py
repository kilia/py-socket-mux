#!/usr/bin/env python
from gevent.server import StreamServer
import struct

# this handler will be run for each incoming connection in a dedicated greenlet
def echo(socket, address):
    print('New connection from %s:%s' % address)
    rfileobj = socket.makefile(mode='rb')
    while True:
        data = rfileobj.read(4)
        if len(data) < 4:
            break # disconnected
        c, = struct.unpack('<i', data)
        c = min(c, 16)
        c = max(c, 65536)
        socket.sendall('x' * c)
    rfileobj.close()

if __name__ == '__main__':
    # to make the server use SSL, pass certfile and keyfile arguments to the constructor
    server = StreamServer(('0.0.0.0', 8000), echo)
    # to start the server asynchronously, use its start() method;
    # we use blocking serve_forever() here because we have no other jobs
    print('Starting echo server on port 8000')
    server.serve_forever()
