import sys, struct, time
import gevent
from gevent import socket

address = ('104.224.140.44', 9000)

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.connect(address)
#print('Sending %s bytes to %s:%s' % ((len(message), ) + address))

def sender(sock, packets, speed_limit = 25000):
    p = range(packets)
    batch = 100
    starttime = time.time()
    while len(p) > 0:
        t0 = time.time()
        for i in xrange(batch):
            if len(p) == 0:
                break
            sock.send(struct.pack('<i', p.pop()))
        dt = time.time() - t0
        dt = batch * 1./speed_limit - dt
        if dt > 0:
            #print 'sleeping', dt
            gevent.sleep(dt)
    print 'sent all', (time.time() - starttime)

def receiver(sock, packets, timeout = 100.):
    end = time.time() + timeout
    s = set(xrange(packets))
    rc = []
    rs = []
    sock.settimeout(1.0)
    try:
        while time.time() < end:
            data, address = sock.recvfrom(8192)
            i, j = struct.unpack('<ii', data[:8])
            #print 'received', i, j
            #received.append((i, j))
            rc.append(i)
            rs.append(j)
            s.remove(i)
    except Exception as err:
        print err
    print len(rc), len(s)
    print max(rs)-min(rs)


packets = 10000
greenlets = [
    gevent.spawn(sender,sock, packets),
    gevent.spawn(receiver,sock, packets)
]

gevent.joinall(greenlets)