# -*- coding: utf-8 -*-
from __future__ import annotations
import itsdangerous

# -- prioritized --
from gevent import monkey
monkey.patch_all()

# -- stdlib --
import logging
import base64
import sys

# -- third party --
from gevent import signal
from gevent.pool import Pool
import gevent

# -- own --
from client.core import Core
from core import CoreRunner
from thb.bot import BotUserInputHandler
from utils.events import EventHub
import utils
import msgpack
import utils.log


# -- code --
MAIN = gevent.getcurrent()
MAIN.gr_name = 'MAIN'


def wait():
    gevent.idle(-100)
    gevent.sleep(0.01)
    gevent.idle(-100)


class EventTap(object):

    def __init__(self):
        self._taps = {}

    def tap(self, *cores):
        for core in cores:
            for k in dir(core.events):
                if k.startswith('__'):
                    continue

                hub = getattr(core.events, k)
                if not isinstance(hub, EventHub):
                    continue

                def tapper(ev, hub=hub):
                    self._taps[hub] = ev
                    return ev

                hub += tapper

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

    def wait(self, *hubs):
        while True:
            for hub in hubs:
                if hub in self._taps:
                    return
            gevent.sleep(0.01)


SIGNER = itsdangerous.TimestampSigner('ew&(_dc#t346(!qzan_paw2^5f3r)3g80)1l+s_e%7&!a7nr$-')


def get_token(n):
    data = base64.b64encode(msgpack.dumps({'type': 'user', 'id': n + 2}))
    return SIGNER.sign(data).decode('utf-8')


def run_bot(n, server, mode, delay):
    log = logging.getLogger('bot')
    log.info('Bot %s starting', n)
    core = Core(disables=['gate'])  # type: ignore
    runner = CoreRunner(core)
    tap = EventTap()
    tap.tap(core)
    gevent.spawn(runner.run)
    runner.ready.wait()

    def on_observe(pid: int) -> None:
        core.observe.grant(pid, True)
        return pid

    core.events.observe_request += on_observe

    log.info('Bot %s connecting', n)
    rst = core.server.connect(server)
    assert rst == 'success'

    log.info('Bot %s auth', n)
    core.auth.login(get_token(n))
    tap.wait(core.events.auth_success)
    core.matching.start([mode])

    log.info('Bot %s waiting game start', n)
    tap.wait(core.events.game_joined)
    g = tap[core.events.game_joined]
    g.event_observer = BotUserInputHandler(g, delay=delay)
    core.room.get_ready()
    tap.wait(core.events.game_started)

    log.info('Bot %s start reacting', n)
    core.game.start_game(g)
    tap.wait(
        core.events.game_ended,
        core.events.client_game_finished,
        core.events.game_crashed,
    )

    log.info('Bot %s finished', n)
    core.result.set('done')


def start_bot():
    def _exit_handler(*a, **k):
        gevent.kill(MAIN, SystemExit)

    signal.signal(signal.SIGTERM, _exit_handler)

    import argparse

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--server', default='tcp://127.0.0.1:9999', type=str)
    parser.add_argument('--mode', default='THBattle2v2', type=str)
    parser.add_argument('--bots', default=3, type=int)
    parser.add_argument('--delay', default=0.0, type=float)
    options = parser.parse_args()

    import settings
    utils.log.init_server('INFO', '', settings.VERSION, '')

    pool = Pool(10)
    for i in range(options.bots):
        pool.spawn(run_bot, i, options.server, options.mode, options.delay)

    pool.join()


start_bot()
