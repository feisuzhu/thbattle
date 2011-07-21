import gevent
from gevent.queue import Queue
from gevent import Timeout
import simplejson as json


class Client(object):
    
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.link_state = 'connected' # or disconnected
        self.queue = Queue(maxsize=100)

    def send(self, p):
        '''
        Send packet, p must be a dict or has a 'get_dict' method
        '''
        if self.link_state == 'connected':
            if isinstance(p, dict):
                d = p
            else:
                d = p.get_dict()
            self.sock.send(json.dumps(d))
        else:
            return False

    def close(self):
        self.link_state = 'disconnected'
        sock.close()
    
    def recv(self):
        return self.queue.get()

    def _recv(self):
        while True:
            if self.link_state == 'connected':
                with Timeout(3, None):
                    s = self.sock.makefile().readline()
                    self.queue.put(json.loads(s), block=False)
            else:
                return None

            
