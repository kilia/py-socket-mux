import gevent
from gevent import socket
from gevent import queue

import tcptunnel as tcp

def server_con():
    sock = socket.socket()
    addr = ('localhost', 51080)
    sock.connect(addr)
    print sock, 'connected to', addr
    return sock

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
    
