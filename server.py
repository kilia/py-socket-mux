import gevent
from gevent import socket
from gevent import queue

import tcptunnel as tcp

tcp.conversation = tcp.Conversation('server')
tcp.tunnel = tcp.Tunnel()

class dummy_socket(object):
    def __init__(self, filename):
        self._fd = open(filename, 'wb')
        self._seq = 0
        self._echoq = queue.Queue()
        
    def send(self, data):
        self.sendall(data)
        self._echoq.put(data)
        
    def recv(self, size):
        return queue.get()
        
    def sendall(self, data):
        #print 'send', len(data), data, [ord(c) for c in data]
        self._fd.write(data)
        self._fd.flush()
        print 'write', len(data), 'bytes'
        #gevent.sleep(0.1)

def server_con():
    return dummy_socket('server.out')
tcp.make_server_connection = server_con

def listen():
    server = socket.socket()
    server.bind(('0.0.0.0', 500))
    print 'server bind on:', server
    server.listen(500)
    while True:
        sock, addr = server.accept()
        print addr, 'connected'
        t = tcp.TcpTunnel(sock, tcp.conversation)
        tcp.tunnel.add_tunnel(t)
        gevent.spawn(t.send_to_conversation)

gevent.spawn(listen).join()