# -*- coding: utf-8 -*-

# -- stdlib --
from collections import deque
import logging
log = logging.getLogger('network')

# -- third party --
from gevent import getcurrent
from gevent.event import Event

# -- own --
from utils import Packet, instantiate
from .endpoint import EndpointDied

# -- code --


class GamedataMixin(object):
    @instantiate
    class NODATA(object):
        def __repr__(self):
            return 'NODATA'

    def init_gamedata_mixin(self):
        self.gdqueue = deque(maxlen=100000)
        self.gdevent = Event()
        self._in_gexpect = False

    def gamedata(self, data):
        p = Packet(data)
        self.gdqueue.append(p)
        self.gdevent.set()

    def gexpect(self, tag, blocking=True):
        try:
            assert not self._in_gexpect, 'NOT REENTRANT'
            self._in_gexpect = True
            blocking and log.debug('GAME_EXPECT: %s', repr(tag))
            l = self.gdqueue
            e = self.gdevent
            e.clear()

            glob = False
            if tag.endswith('*'):
                tag = tag[:-1]
                glob = True

            while True:
                for i, packet in enumerate(l):
                    if isinstance(packet, EndpointDied):
                        raise packet

                    if packet[0] == tag or (glob and packet[0].startswith(tag)):
                        log.debug('GAME_READ: %s', repr(packet))
                        del l[i]
                        return packet

                    else:
                        log.debug('GAME_DATA_MISS: %s', repr(packet))
                        log.debug('EXPECTS: %s, GAME: %s', tag, getcurrent())

                if blocking:
                    e.wait(timeout=5)
                    e.clear()
                else:
                    e.clear()
                    return None, self.NODATA
        finally:
            self._in_gexpect = False

    def gclear(self):
        '''
        Clear the gamedata queue,
        used when a game starts, to eliminate data from last game,
        which confuses the new game.
        '''
        self.gdqueue.clear()

    def gbreak(self):
        # is it a hack?
        # XXX: definitly, and why it's here?! can't remember
        # Explanation:
        # Well, when sb. exit game in input state,
        # the others must wait until his timeout exceeded.
        # called by gamehall.exit_game to break such condition.
        self.gdqueue.append(EndpointDied())
        self.gdevent.set()
