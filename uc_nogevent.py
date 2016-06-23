#from gevent import monkey
#monkey.patch_all()

import sys, struct, time
#import gevent
#from gevent import socket, queue
import socket
import Queue as queue
from sys import stdout, stderr

#address = ('104.224.140.44', 9000)
address = ('127.0.0.1', 9000)

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.connect(address)
#print('Sending %s bytes to %s:%s' % ((len(message), ) + address))

M = 50000

w = stderr.write

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
            #gevent.sleep(dt)
            pass
    stderr.write('sent all in %.2f sec\n' % (time.time() - starttime))

def receiver(sock, packets, q):
    #s = set(xrange(packets))
    rs = []
    sock.settimeout(1.0)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1024*1024*10)
    w('buffer:%d'%sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))
    
    try:
        while True:
            data, address = sock.recvfrom(8192)
            i, = struct.unpack('<i', data[:4])
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

    w('\nrs size is %d:' % len(rs))
    #for r in rs:
    #    w('%d '%r)
    stderr.write('\nmissing:')
    missing = set(xrange(packets)).difference(set(rs))
    for m in missing:
        w('%d ' % m)
    stderr.write('\nout of order:')
    _max_ = -1
    for r in rs:
        if r < _max_:
            stderr.write('%d ' % r)
        _max_ = max(r, _max_)
    stderr.write('\n')

def counter(q, t0):
    #t0 = time.time()
    ts = 0
    while True:
        data = q.get()
        if data is None:
            break
        ts += len(data)
    dt = time.time() - t0
    w('total %d bytes, in %.3f sec. ~%.2fMB/s\n' % (ts, dt, ts/1024./1024./dt))
        
t0 = time.time()
packets = M
q = queue.Queue()
#greenlets = [
#    gevent.spawn(sender,sock, packets/M, M),
#    gevent.spawn(receiver,sock, packets, q),
#    gevent.spawn(counter, q)
#]

#gevent.joinall(greenlets)
sender(sock,1,M)
receiver(sock, packets, q)
counter(q, t0)