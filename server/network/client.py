import gevent
from gevent.queue import Queue
from gevent import Timeout
from gevent import socket
import simplejson as json

class Client(object):
    
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.link_state = 'connected' # or disconnected
        self.queue = Queue(100)
        self.send = self.sock.send
        self.recv = self.sock.recv
        self.active_queue = None # if this is not none, data will send to this queue as (self, data)

    def write(self, p):
        '''
        Send json encoded packet, p must be a dict or has a '__data__' method
        '''
        if self.link_state == 'connected':
            if isinstance(p, dict):
                d = p
            else:
                d = p.__data__()
            self.send(json.dumps(d) + "\n")
        else:
            return False

    def close(self):
        self.link_state = 'disconnected'
        self.sock.close()
    
    def read(self):
        return self.queue.get()

    def _greenlet_waitdata(self):
        while True:
            f = self.sock.makefile()
            if self.link_state == 'connected':
                with Timeout(30, False):
                    try:
                        s = f.readline(200)
                        if s == '':
                            self.close()
                            return
                        d = json.loads(s)
                        if d.has_key('heartbeat'):
                            continue
                        if self.active_queue:
                            self.active_queue.put((self,d))
                        else:
                            self.queue.put(d, block=False)
                    except json.JSONDecodeError as e:
                        self.write(dict(info='Incorrect format'))
                    except socket.IOError as e:
                        self.close()
            else:
                return
