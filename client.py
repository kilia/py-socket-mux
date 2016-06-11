import gevent
from gevent import socket

import tcptunnel as tcp

tcp.conversation = tcp.Conversation('client')
tcp.tunnel = tcp.Tunnel()

class dummy_socket(object):
    def __init__(self, filename):
        self._fd = open(filename, 'wb')
        self._rfd = open('tcptunnel.pyc','rb')
        self._seq = 0
        
    def send(self, data):
        self.sendall(data)
        
    def recv(self, size):
        gevent.sleep(1.0)
        #self._seq += 1
        #return '%010d\n' % self._seq
        return self._rfd.read(1024)
        
    def sendall(self, data):
        #print 'send', len(data), data, [ord(c) for c in data]
        self._fd.write(data)
        self._fd.flush()
        print 'write', len(data), 'bytes'
        #gevent.sleep(0.1)

def client():
    c = socket.socket()
    c.connect(('127.0.0.1',500))
    print 'connected'
    t = tcp.TcpTunnel(c, tcp.conversation)
    print 'add to tunnel'
    tcp.tunnel.add_tunnel(t)
    print 'tunnel send_to_conversation'
    gevent.spawn(t.send_to_conversation)

sock = dummy_socket('client.out')
w = tcp.Window(sock, tcp.conversation)

greenlets = []    
for _ in xrange(4):
    c = gevent.spawn(client)
    greenlets.append(c)
#greenlets.append(ws)
gevent.joinall(greenlets)

ws = gevent.spawn(w.start)
ws.join()
