import gevent
from gevent import socket
from gevent import queue

import tcptunnel as tcp

def server_con():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addr = ('localhost', 5454)
    #addr = ('localhost', 51080)
    sock.connect(addr)
    print sock, 'connected to', addr
    return sock

PORT = 52000
# make a server tunnel listening on '0.0.0.0:$PORT$'
sever_tunnel = tcp.Tunnel('server', server_con)
g = gevent.spawn(sever_tunnel.tcp_listen, ('0.0.0.0', PORT))
g.join()
