# -*- coding: utf-8 -*-

# -- stdlib --
import logging
log = logging.getLogger("Client")

# -- third party --
from gevent import Greenlet, Timeout

# -- own --
from .common import GamedataMixin
from network import Endpoint, EndpointDied
from utils import BatchList, log_failure

# -- code --


__all__ = ['Client']


class Client(Endpoint, GamedataMixin, Greenlet):
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.observers = BatchList()
        self.init_gamedata_mixin()

    @log_failure(log)
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
                with Timeout(90, False):
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

    def handle_command(self, cmd, data):
        raise NotImplementedError

    def handle_drop(self):
        raise NotImplementedError

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
