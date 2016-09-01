# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --
from gevent import Greenlet
from gevent.queue import Channel
import gevent

# -- own --
from client.core.common import ForcedKill
from endpoint import Endpoint
from game.base import Gamedata


# -- code --
log = logging.getLogger('client.core.endpoint')


class Server(Endpoint, Greenlet):
    '''
    Used at client side, to represent server
    '''

    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.ctlcmds = Channel()
        self.gamedata = Gamedata(recording=True)

    def _run(self):
        while True:
            cmd, data = self.read()
            if cmd == 'gamedata':
                self.gamedata.feed(data)
            else:
                self.ctlcmds.put([cmd, data])

    def gexpect(self, tag, blocking=True):
        return self.gamedata.gexpect(tag, blocking)

    def gbreak(self):
        return self.gamedata.gbreak()

    def gclear(self):
        self.gamedata = Gamedata(recording=True)

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))
        encoded = self.encode(['gamedata', [tag, data]])
        self.raw_write(encoded)

    def wait_till_live(self):
        self.gamedata.wait_empty()

    def gamedata_piled(self):
        return len(self.gamedata.gdqueue) > 60

    def shutdown(self):
        self.kill()
        self.join()
        self.ctlcmds.put(['shutdown', None])
        self.close()


class ReplayEndpoint(object):
    def __init__(self, replay, game):
        self.gdlist = list(replay.gamedata)
        self.game = game

    def gexpect(self, tag):
        if not self.gdlist:
            gevent.sleep(3)
            raise ForcedKill

        glob = False
        if tag.endswith('*'):
            tag = tag[:-1]
            glob = True

        for i, d in enumerate(self.gdlist):
            if d[0] == tag or (glob and d[0].startswith(tag)):
                del self.gdlist[i]
                return d

        gevent.sleep(3)
        raise ForcedKill

    def gwrite(self, tag, data):
        pass

    def gclear(self):
        pass

    def gbreak(self):
        pass

    def end_replay(self):
        self.game.kill()
