import gevent
from gevent import socket
from gevent import queue

import tcptunnel as tcp

PORT = 52000

# make a client tunnel ann connect to server, X default count(8) connections
client_tunnel = tcp.Tunnel('client')
remote_addr = ('104.224.140.44', PORT)
#remote_addr = ('127.0.0.1', PORT)
client_tunnel.tcp_connect(remote_addr, 80)

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
    
