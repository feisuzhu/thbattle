from gevent import Greenlet, Timeout
from gevent.queue import Queue
from gevent.event import Event
from network import Endpoint, EndpointDied
import logging
import sys

from collections import deque

log = logging.getLogger("Server")

class Packet(list): # compare by identity list
    __slots__ = ('scan_count')
    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

    def __ne__(self, other):
        return self.__eq__(other)

class Server(Endpoint, Greenlet):

    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.gdqueue = deque(maxlen=100)
        self.read_timeout = 120
        self.ctlcmds = []
        self.userid = 0
        self.ctlcmds_event = Event()
        self.gdevent = Event()

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
        l = self.gdqueue
        if len(l) >= 100:
            log.warn('GAMEDATA LIST TOO LONG, KILLING')
            self.instant_kill()
        else:
            p = Packet(data)
            p.scan_count = 0
            l.append(p)
            self.gdevent.set()

    def gexpect(self, tag):
        l = self.gdqueue
        e = self.gdevent
        while True:
            for i in xrange(len(l)):
                d = l.popleft()
                if d[0] == tag:
                    return d[1]
                else:
                    d.scan_count += 1
                    if d.scan_count >= 5:
                        log.warn('Dropped gamedata: %s' % d)
                    else:
                        l.append(d)
            e.clear()
            e.wait()

    def gwrite(self, tag, data):
        self.write(['gamedata', [tag, data]])

    def _ctldata(self, cmd, data):
        self.ctlcmds.append([cmd, data])
        self.ctlcmds_event.set()

    def ctlexpect(self, cmdlst):
        l = self.ctlcmds
        e = self.ctlcmds_event
        while True:
            for i, v in enumerate(l):
                if v[0] in cmdlst:
                    del l[i]
                    return v
            e.clear()
            e.wait()
