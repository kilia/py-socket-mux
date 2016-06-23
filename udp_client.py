import sys, struct, time
import gevent
from gevent import socket, queue
from sys import stdout, stderr

#address = ('104.224.140.44', 9000)
address = ('127.0.0.1', 9000)

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.connect(address)
#print('Sending %s bytes to %s:%s' % ((len(message), ) + address))

M = 200

def sender(sock, packets, multi, speed_limit = 1000):
    p = [multi for i in xrange(packets)]
    batch = int(1)
    starttime = time.time()
    while len(p) > 0:
        t0 = time.time()
        for i in xrange(batch):
            if len(p) == 0:
                break
            sock.send(struct.pack('<i', p.pop()))
        dt = time.time() - t0
        dt = batch * 1./speed_limit - dt
        if dt > 0.0:
            #stderr.write('sleeping %.2f sec\n' % dt)
            gevent.sleep(dt)
    stderr.write('sent all in %.2f sec\n' % (time.time() - starttime))

def receiver(sock, packets, q):
    #s = set(xrange(packets))
    rs = []
    sock.settimeout(1.0)
    try:
        while True:
            data, address = sock.recvfrom(8192)
            i = struct.unpack('<i', data[:4])
            #print 'received', i, j
            #received.append((i, j))
            rs.append(i)
            #s.remove(i)
            q.put(data[4:])
    except Exception as err:
        stderr.write('%s %s\n' % (str(type(err)), str(err)))
    lost = packets - len(rs)
    stderr.write('total %d packets, %d(%.2f%%) missing\n' % (packets, lost, (lost*100./packets)))
    q.put(None)

def counter(q):
    while True:
        data = q.get()
        if data is None:
            break
        stdout.write(data)

packets = 100000
q = queue.Queue()
greenlets = [
    gevent.spawn(sender,sock, packets/M, M),
    gevent.spawn(receiver,sock, packets, q),
    gevent.spawn(counter, q)
]

gevent.joinall(greenlets)