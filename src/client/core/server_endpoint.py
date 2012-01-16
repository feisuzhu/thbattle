from gevent import Greenlet, Timeout
from gevent.queue import Queue
from gevent.event import Event
from network import Endpoint, EndpointDied
import logging
import sys

log = logging.getLogger("Server")

class Server(Endpoint, Greenlet):
    
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.gdqueue = Queue(100)
        self.read_timeout = 120
        self.ctlcmds = []
        e = Event()
        e.clear()
        self.ctlcmds_event = e

    def _run(self):
        try:
            while True:
                cmd, data = self.read(timeout=self.read_timeout)
                if cmd == 'gamedata':
                    self._gamedata(data)
                else:
                    self._ctldata(cmd, data)
        except EndpointDied:
            pass

        except Timeout:
            self.close()
       
    def _gamedata(self, data):
        if not self.gdqueue.full():
            self.gdqueue.put(data)

    def gread(self):
        return self.gdqueue.get()

    def gexpect(self, tag):
        while True:
            d = self.gread()
            if d[0] == tag:
                return d[1]
           #else: drop
    
    '''
    # enable it when needed, since it's just a thought
    def gexpect_with_tle(self, tag):
        while True:
            d = self.gread()
            if d[0] == 'client_tle':
                import game.TimeLimitExceeded
                raise game.TimeLimitExceeded
            if d[0] == tag:
                return d[1]
           #else: drop
    '''
    def gwrite(self, data):
        self.write(['gamedata', data])

    def _ctldata(self, cmd, data):
        self.ctlcmds.append([cmd, data])
        self.ctlcmds_event.set()

    def ctlexpect(self, cmdlst):
        while True:
            for i, v in enumerate(self.ctlcmds):
                if v[0] in cmdlst:
                    del self.ctlcmds[i]
                    return v
            self.ctlcmds_event.clear()
            self.ctlcmds_event.wait()
