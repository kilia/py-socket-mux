import gevent
from gevent import socket
from gevent import queue

import tcptunnel as tcp

#tcp.conversation = tcp.Conversation('server')
#tcp.tunnel = tcp.Tunnel()

class dummy_echo_socket(object):
    def __init__(self, filename):
        self._fd = open(filename, 'wb')
        self._seq = 0
        self._echoq = queue.Queue()
        
    def send(self, data):
        self.sendall(data)
        
    def recv(self, size):
        data = self._echoq.get()
        print 'send %d bytes to client' % len(data)
        return data
        
    def sendall(self, data):
        #print 'send', len(data), data, [ord(c) for c in data]
        self._fd.write(data)
        self._fd.flush()
        print 'server write', len(data), 'bytes'
        self._echoq.put(data)
        #gevent.sleep(0.1)

def server_con():
    return dummy_echo_socket('server.out')

PORT = 500

sever_tunnel = tcp.Tunnel('server', server_con)
gevent.spawn(sever_tunnel.tcp_listen, ('0.0.0.0', PORT))
# ? join ?

client_tunnel = tcp.Tunnel('client')

class dummy_socket(object):
    def __init__(self, filename):
        self._fd = open(filename, 'wb')
        self._rfd = open('tcptunnel.pyc','rb')
        self._seq = 0
        
    def send(self, data):
        self.sendall(data)
        
    def recv(self, size):
        #gevent.sleep(0.1)
        #self._seq += 1
        #return '%010d\n' % self._seq
        data = self._rfd.read(size)
        if len(data) == 0:
            print 'finished reanding'
            while True:
                gevent.sleep(1.0)
                quit()
        return data
        
    def sendall(self, data):
        #print 'send', len(data), data, [ord(c) for c in data]
        self._fd.write(data)
        self._fd.flush()
        print 'client write', len(data), 'bytes'
        #gevent.sleep(0.1)

sock = dummy_socket('client.out')
w = tcp.Window(sock, client_tunnel.get_conversation())

client_tunnel.tcp_connect(('127.0.0.1',PORT))

ws = gevent.spawn(w.start)
ws.join()
