# -*- coding: utf-8 -*-
from gevent import Greenlet
from gevent.queue import Queue
from network import Endpoint
import logging

log = logging.getLogger("Server")

from .common import GamedataMixin


class Server(Endpoint, GamedataMixin, Greenlet):
    '''
    Used at client side, to represent server
    '''

    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.ctlcmds = Queue(0)
        self.userid = 0
        self.init_gamedata_mixin()

    def _run(self):
        while True:
            cmd, data = self.read()
            if cmd == 'gamedata':
                self.gamedata(data)
            else:
                self.ctlcmds.put([cmd, data])

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))
        encoded = self.encode(['gamedata', [tag, data]])
        self.raw_write(encoded)
