#!/usr/bin/env python
from gevent import socket
from gevent import queue
import gevent

import struct
from sys import stdout, stderr
import sys
import time

addr = ('104.224.140.44', 8000)
#addr = ('localhost', 8000)
batch = 16000
threads = 64

try:
    threads = int(sys.argv[1])
    stderr.write('%d threads\n' % threads)
except:
    pass

q = queue.Queue()

socks = queue.Queue()

def connector():
    global socks, addr
    client_sock = socket.socket()
    client_sock.connect(addr)
    socks.put(client_sock)

def reader():
    global q, addr
    client_sock = socks.get()
    fobj = client_sock.makefile(mode='rb')
    cmd = struct.pack('<i', batch)
    while True:
        #fobj.write(cmd)
        #fobj.flush()
        client_sock.sendall(cmd)
        '''data = fobj.read(batch)
        if len(data) != batch:
            break'''
        data = client_sock.recv(80000)
        q.put(data)
    fobj.close()

total_bytes = 0
def counter():
    global q, total_bytes
    while True:
        data = q.get()
        stdout.write(data)
        total_bytes += len(data)    

greenlets = []
stderr.write('connecting to %s X %d threads\n' % (addr, threads))
for _ in xrange(threads):
    greenlets.append(gevent.spawn(connector))
t0 = time.time()
gevent.joinall(greenlets)
t1 = time.time()
stderr.write('all connected in %.2f sec.\n' % (t1 - t0))

greenlets = []
for _ in xrange(threads):
    greenlets.append(gevent.spawn(reader))
greenlets.append(gevent.spawn(counter))

with gevent.Timeout(60., False):
    gevent.joinall(greenlets)

t2 = time.time()
stderr.write('finished, %.2f KB/s\n' % (total_bytes/1024./(t2-t1)))

if __name__ == '__main__':
    pass