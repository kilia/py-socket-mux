import struct, random, Queue

from config import log

''' 
client - window - conversation - tunnel ~ tunnel - conversation - window - server
'''

class Window(object):
    '''
    suppose no packet will be lost, but the order may be chaos.
    deal with the out of order problem with a window algorithm.
    '''
    def __init__(self, sock, max_window_size = 256):
        assert(sock is not None)
        self._sock = sock
        self._si = self._ri = 0 # si ~ sending index, ri ~ receive index
        self._rbuffer = {}
        self._mws = max_window_size
        
    def send(self, data): # sending needs no buffering
        self._sock.send(struct.pack('<i',self._si) + data)
        self._si += 1
        
    def recv(self): # use a dict to reorder the sequence
        while True:
            buf = self._sock.recv()
            if buf is None:
                break
            assert(len(buf) > 4)
            sid, = struct.unpack('<i',buf[:4])
            assert(0 <= (sid - self._ri) <= self._mws)
            data = buf[4:]
            self._rbuffer[sid] = data
        data = self._rbuffer.get(_ri, None)
        if not data is None:
            self._ri += 1
            del(self.__rbuffer[_ri])
        return data
            
class ConversationManager(object):
    def __init__(self, tunnel):
        self._tunnel = tunnel
        self._buffer = {}
    
    def send(self, cid, data):
        self._tunnel.send(struct.pack('<Q',cid) + data)
    
    def recv(self, cid):
        while True:
            buf = self._tunnel.recv()
            if buf is None:
                break
            assert(len(buf) > 8)
            cid, = struct.unpack('<Q',buf[:8])
            data = buf[8:]
            q = self._buffer.get(cid,Queue.Queue())
            q.put(data)
        q = self._buffer.get(cid,Queue.Queue())
        if not q.empty():
            return q.get()
    
    def get_conversation(self):
        cid = random.getrandbits(64)
        return Conversation(cid, self)

class Conversation(object):
    '''
    multiple conversation will be in the same socket,
    we must have a way to distinquish each of them.
    we try to do this by assign a unique ID to each conversation
    '''
    def __int__(self, cid, sock):
        self._cid = cid #Conversation.get_conversation_id()
        self._sock = sock
        
    def send(self, data):
        self._sock.send(self._cid, data)
        
    def recv(self):
        return self._sock.recv(self._cid)
        