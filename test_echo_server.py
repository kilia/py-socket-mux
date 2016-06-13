import gevent
from gevent import socket
from gevent import queue

import tcptunnel as tcp

#tcp.conversation = tcp.Conversation('server')
#tcp.tunnel = tcp.Tunnel()

class dummy_echo_socket(object):
    def __init__(self):
        self._seq = 0
        self._echoq = queue.Queue()
        
    def send(self, data):
        self.sendall(data)
        
    def recv(self, size):
        data = self._echoq.get()
        print 'send %d bytes to client' % len(data)
        return data
        
    def sendall(self, data):
        if len(data)>0:
            self._echoq.put(data)
        
    def close(self):
        pass

def server_con():
    return dummy_echo_socket()

PORT = 500

# make a server tunnel listening on '0.0.0.0:$PORT$'
sever_tunnel = tcp.Tunnel('server', server_con)
gevent.spawn(sever_tunnel.tcp_listen, ('0.0.0.0', PORT))

# make a client tunnel ann connect to server, X default count(8) connections
client_tunnel = tcp.Tunnel('client')
client_tunnel.tcp_connect(('127.0.0.1',PORT))

# listen to accept a REAL client
server_sock = socket.socket()
addr = ('0.0.0.0', PORT + 1)
server_sock.bind(addr)
print 'REAL server bind on:', addr
server_sock.listen(500)
while True:
    sock, addr = server_sock.accept()
    print addr, 'connected'
    w = tcp.Window(sock, client_tunnel.get_conversation())
    ws = gevent.spawn(w.start)
    
