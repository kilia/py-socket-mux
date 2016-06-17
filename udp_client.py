import sys, struct, time
import gevent
from gevent import socket

address = ('localhost', 9000)

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.connect(address)
#print('Sending %s bytes to %s:%s' % ((len(message), ) + address))

def sender(sock, packets):
    for i in xrange(packets):
        print 'sending', i
        sock.send(struct.pack('<i', i))

def receiver(sock, packets, timeout = 10.):
    end = time.time() + timeout
    received = []
    while time.time() < end:
        data, address = sock.recvfrom(8192)
        i, j = struct.unpack('<ii', data[:8])
        print 'received', i, j
        received.append(data)
    print len(received)

packets = 100
greenlets = [
    gevent.spawn(sender,sock, packets),
    gevent.spawn(receiver,sock, packets)
]

gevent.joinall(greenlets)