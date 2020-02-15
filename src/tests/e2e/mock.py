# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging
import random

# -- third party --
from gevent.pool import Pool
import gevent

# -- own --
from core import CoreRunner
from server.parts.backend import MockBackend
import client.core
import server.core


# -- code --
log = logging.getLogger('mock')


def enable_endpoint_logging():
    import endpoint
    endpoint.log.setLevel(logging.DEBUG)


class EventTap(object):

    def __init__(self):
        self._taps = {}

    def __iadd__(self, hub):
        def tapper(ev):
            self._taps[hub] = ev
            return ev
        hub += tapper
        return self

    def tap_all(self, lst):
        for h in lst:
            self += h

    def __getitem__(self, k):
        return self._taps[k]


class Environ(object):
    def __init__(self):
        self.pool = Pool(32)
        p = random.randint(10000, 30000)
        self.rendezvous = f'tcp://127.0.0.233:{p}'
        self.parent = gevent.getcurrent()

    def _run(self, runner):
        try:
            runner.run()
        except Exception as e:
            gevent.kill(self.parent, e)

    def client_core(self) -> client.core.Core:
        core = client.core.Core(disables=['warpgate'], paranoid=True)
        runner = CoreRunner(core)
        self.pool.spawn(self._run, runner)
        runner.ready.wait()
        core.server.connect(self.rendezvous)
        return core

    def server_core(self) -> server.core.Core:
        core = server.core.Core(disables=[
            'archive', 'connect', 'stats', 'backend'
        ], listen=self.rendezvous, paranoid=True)
        core.backend = MockBackend(core)
        runner = CoreRunner(core)
        self.pool.spawn(self._run, runner)
        gevent.sleep(0.05)
        return core

    def shutdown(self):
        self.pool.kill()
