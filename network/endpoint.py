import gevent
from gevent import Greenlet, Timeout, socket
from gevent.queue import Queue
import simplejson as json
import logging

log = logging.getLogger("Endpoint")

class EndpointDied(Exception):
    pass

class Endpoint(object):
    
    def __init__(self, sock, address):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock = sock
        self.address = address
        self.link_state = 'connected' # or disconnected

    @staticmethod
    def encode(p):
        def default(o):
            return o.__data__() if hasattr(o, '__data__') else repr(o)
        return json.dumps(p, default=default) + "\n"
    
    def raw_write(self, s):
        if self.link_state == 'connected':
            self.sock.send(s)
        else:
            log.debug('Write after disconnected: %s' % s)
            return False
    
    def write(self, p):
        '''
        Send json encoded packet
        '''
        self.raw_write(self.encode(p))


    def close(self):
        if not self.link_state == 'disconnected':
            self.link_state = 'disconnected'
            self.sock.close()
    
    def read(self, timeout=60):
        f = self.sock.makefile()
        while True:
            with Timeout(timeout, None):
                try:
                    s = f.readline(1000)
                    if s == '':
                        self.close()
                        raise EndpointDied()    
                    d = json.loads(s)
                    return d    
                except json.JSONDecodeError as e:
                    self.write(['bad_format', None])
                    continue
                except IOError as e:
                    self.close()
                    raise EndpointDied()
