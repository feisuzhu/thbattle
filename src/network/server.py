# -*- coding: utf-8 -*-

# -- stdlib --
import logging
log = logging.getLogger("Client")

# -- third party --
from gevent import Greenlet, Timeout
import simplejson as json

# -- own --
from .common import GamedataMixin
from network import Endpoint, EndpointDied
from utils import BatchList

# -- code --


__all__ = ['Client']


class Client(Endpoint, GamedataMixin, Greenlet):
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.observers = BatchList()
        self.init_gamedata_mixin()
        self.gdhistory = []
        self.usergdhistory = []

    def _run(self):
        self.account = None

        # ----- Banner -----
        from settings import VERSION
        self.write(['thbattle_greeting', VERSION])
        # ------------------

        self.state = 'connected'
        while True:
            try:
                hasdata = False
                with Timeout(30, False):
                    cmd, data = self.read()
                    hasdata = True

                if not hasdata:
                    self.close()
                    # client should send heartbeat periodically
                    raise EndpointDied

                if cmd == 'gamedata':
                    self.gamedata(data)
                else:
                    self.handle_command(cmd, data)

            except EndpointDied:
                self.gbreak()
                break

        # client died, do clean ups
        self.handle_drop()

    def gexpect(self, tag, blocking=True):
        tag, data = GamedataMixin.gexpect(self, tag, blocking)
        tag and self.usergdhistory.append((self.player_index, tag, data))
        return tag, data

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))
        encoded = self.encode(['gamedata', [tag, data]])
        self.raw_write(encoded)
        self.gdhistory.append([tag, json.loads(self.encode(data))])
        self.observers and self.observers.raw_write(encoded)

    def replay(self, ob):
        for data in self.gdhistory:
            ob.raw_write(json.dumps(['gamedata', data]) + '\n')

    def __data__(self):
        return [self.account.userid, self.account.username, self.state]

    def close(self):
        Endpoint.close(self)
        self.kill(EndpointDied)

    def __repr__(self):
        acc = self.account
        if not acc:
            return Endpoint.__repr__(self)

        return '%s:%s:%s' % (
            self.__class__.__name__,
            self.address[0],
            acc.username.encode('utf-8'),
        )


class DroppedClient(Endpoint):
    read = write = raw_write = gclear = lambda *a, **k: None

    def __init__(self, client=None):
        client and self.__dict__.update(client.__dict__)

    def gwrite(self, tag, data):
        self.gdhistory.append([tag, json.loads(self.encode(data))])

    def gexpect(self, tag, blocking=True):
        raise EndpointDied

    @property
    def state(self):
        return 'dropped'

    @state.setter
    def state(self, val):
        pass
