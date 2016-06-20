#!/usr/bin/env python
from gevent import socket
from gevent import queue
import gevent

import struct
from sys import stdout

addr = ('localhost', 8000)
batch = 16000
threads = 64

q = queue.Queue()

def reader():
    global q, addr
    client_sock = socket.socket()
    client_sock.connect(addr)
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

def counter():
    global q
    while True:
        data = q.get()
        stdout.write(data)    

greenlets = []
print 'connecting to ', addr, ' X', threads
for _ in xrange(threads):
    greenlets.append(gevent.spawn(reader))
greenlets.append(gevent.spawn(counter))

with gevent.Timeout(10., False):
    gevent.joinall(greenlets)
print 'finished'

if __name__ == '__main__':
    pass