# -*- coding: utf-8 -*-
from __future__ import annotations

# -- prioritized --
from gevent import monkey
monkey.patch_all()

# -- stdlib --
from typing import TYPE_CHECKING, Any
import logging
import sys
import urllib.parse

# -- third party --
from gevent import signal
import gevent

# -- own --
import utils
import utils.log

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
MAIN = gevent.getcurrent()
MAIN.gr_name = 'MAIN'

core: Core


def start_server():
    global core

    def _exit_handler(*a, **k):
        gevent.kill(MAIN, SystemExit)

    signal.signal(signal.SIGTERM, _exit_handler)

    import argparse

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('node', type=str)
    parser.add_argument('--listen', default='tcp://0.0.0.0:9999', type=str)
    parser.add_argument('--backdoor', default='tcp://127.0.0.1:19999', type=str)
    parser.add_argument('--log', default='file:///dev/shm/thb.log?level=INFO')
    parser.add_argument('--archive-path', default='file:///dev/shm/thb-archive')
    parser.add_argument('--backend', default='http://token@localhost/graphql')
    parser.add_argument('--interconnect', default='')
    options = parser.parse_args()

    import settings

    log = urllib.parse.urlparse(options.log)
    assert log.scheme == 'file'
    args = dict(urllib.parse.parse_qsl(log.query))
    utils.log.init_server(args.get('level', 'INFO').upper(), settings.SENTRY_DSN, settings.VERSION, log.path)

    from gevent.backdoor import BackdoorServer
    a = urllib.parse.urlparse(options.backdoor)
    gevent.spawn(BackdoorServer((a.hostname, a.port)).serve_forever)

    root = logging.getLogger()
    root.info('=' * 20 + settings.VERSION + '=' * 20)

    from server.core import Core
    from core import CoreRunner

    disables: Any = []  # stupid mypy

    core = Core(
        node=options.node,
        listen=options.listen,
        interconnect=options.interconnect,
        archive_path=options.archive_path,
        backend=options.backend,
        disables=disables,
    )
    runner = CoreRunner(core)
    runner.run()


if __name__ == '__main__':
    start_server()
