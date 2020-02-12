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


class Environ(object):
    def __init__(self):
        self.pool = Pool(32)
        p = random.randint(10000, 30000)
        self.rendezvous = f'tcp://127.0.0.233:{p}'

    def client_core(self) -> client.core.Core:
        core = client.core.Core(disables=['warpgate'])
        runner = CoreRunner(core)
        self.pool.spawn(runner.run)
        runner.ready.wait()
        core.server.connect(self.rendezvous)
        return core

    def server_core(self) -> server.core.Core:
        core = server.core.Core(disables=[
            'archive', 'connect', 'stats', 'backend'
        ], listen=self.rendezvous)
        core.backend = MockBackend(core)
        runner = CoreRunner(core)
        self.pool.spawn(runner.run)
        gevent.sleep(0.05)
        return core

    def shutdown(self):
        self.pool.kill()
