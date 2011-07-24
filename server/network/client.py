import gevent
from gevent import Greenlet
from gevent.queue import Queue
from gevent import Timeout
from gevent import socket
import simplejson as json
import logging

log = logging.getLogger("Client")

class Client(Greenlet):
    
    def __init__(self, sock, address):
        Greenlet.__init__(self)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock = sock
        self.address = address
        self.link_state = 'connected' # or disconnected
        self.queue = Queue(100)
        # self.raw_write = self.sock.send
        # self.raw_recv = self.sock.recv
        self.active_queue = None # if this is not none, data will send to this queue as (self, data)

    @staticmethod
    def encode(p):
        def default(o):
            return o.__data__() if hasattr(o, '__data__') else repr(o)
        return json.dumps(p, default=default) + "\n"
    
    def raw_write(self, s):
        if self.link_state == 'connected':
            self.sock.send(s)
        else:
            log.debug('Write after disconnected')
            return False
    
    def write(self, p):
        '''
        Send json encoded packet
        '''
        self.raw_write(self.encode(p))


    def close(self):
        if not self.link_state == 'disconnected':
            self.link_state = 'disconnected'
            self.sock.shutdown(socket.SHUT_RDWR)
    
    def read(self):
        return self.queue.get()

    def _run(self):
        log.debug("New client")
        f = self.sock.makefile()
        while True:
            with Timeout(30, False):
                try:
                    s = f.readline(1000)
                    if s == '':
                        self.close()
                        return
                    d = json.loads(s)
                    
                    if self.active_queue:
                        self.active_queue.put(d)
                    else:
                        self.queue.put(d, block=False)
                    continue
                except json.JSONDecodeError as e:
                    self.write(dict(info='Incorrect format'))
                    continue
                except IOError as e:
                    self.close()
                    return
            
            # Not receiving data for over 30 secs, drop client
            try:
                self.write(['timeout',None])
            finally:
                self.close()
