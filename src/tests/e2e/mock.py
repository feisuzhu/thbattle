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
from server.parts.connect import MockConnect
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
        self.tap(hub)
        return self

    def tap(self, hub):
        if hub in self._taps:
            raise Exception(f'Already tapped: {hub}')

        def tapper(ev):
            self._taps[hub] = ev
            return ev
        hub += tapper

    def tap_all(self, lst):
        for h in lst:
            self += h

    def take(self, hub):
        v = self._taps[hub]
        del self._taps[hub]
        return v

    def clear(self):
        self._taps.clear()

    def __getitem__(self, k):
        return self._taps[k]

    def __contains__(self, k):
        return k in self._taps


class Environ(object):
    def __init__(self):
        self.pool = Pool(32)
        p = random.randint(10000, 30000)
        ip = random.randint(1, 16777215)
        self.rendezvous = f'tcp://127.{ip}:{p}'
        self.parent = gevent.getcurrent()

    def _run(self, runner):
        try:
            g = gevent.getcurrent()
            g.gr_name = f'Environ.init({runner})'
            runner.run()
        except Exception as e:
            gevent.kill(self.parent, e)

    def client_core(self) -> client.core.Core:
        core = client.core.Core(disables=['warpgate'], testing=True)
        runner = CoreRunner(core, paranoid=True)
        self.pool.spawn(self._run, runner)
        runner.ready.wait()
        core.server.connect(self.rendezvous)
        return core

    def server_core(self) -> server.core.Core:
        core = server.core.Core(disables=[
            'connect', 'stats', 'backend'
        ], listen=self.rendezvous, testing=True)
        core.backend = MockBackend(core)
        core.connect = MockConnect(core)
        runner = CoreRunner(core, paranoid=True)
        self.pool.spawn(self._run, runner)
        gevent.sleep(0.05)
        return core

    def shutdown(self):
        self.pool.kill()
