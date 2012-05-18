# -*- coding: utf-8 -*-
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
        self.gdevent = Event()
        self.read_timeout = 120
        self.ctlcmds = Queue(100)
        self.userid = 0

    def _run(self):
        try:
            while True:
                cmd, data = self.read(timeout=self.read_timeout)
                if cmd == 'gamedata':
                    self._gamedata(data)
                else:
                    self.ctlcmds.put([cmd, data])

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
        log.info('GAME_EXPECT: %s', repr(tag))
        l = self.gdqueue
        e = self.gdevent
        while True:
            for i in xrange(len(l)):
                d = l.popleft()
                if d[0] == tag:
                    log.info('GAME_READ: %s', repr(d))
                    return d[1]
                else:
                    d.scan_count += 1
                    if d.scan_count >= 15:
                        log.warn('Dropped gamedata: %s' % d)
                    else:
                        log.info('GAME_DATA_MISS: %s', repr(d))
                        l.append(d)
            e.clear()
            e.wait()

    def gwrite(self, tag, data):
        self.write(['gamedata', [tag, data]])

    def gclear(self):
        self.gdqueue.clear()
