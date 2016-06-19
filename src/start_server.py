# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- prioritized --
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from gevent import monkey
monkey.patch_all()

# -- stdlib --
import logging
import signal

# -- third party --
from gevent import signal as sig
from gevent.server import StreamServer
import gevent

# -- own --
import utils
import utils.logging

# -- code --
MAIN = gevent.getcurrent()
MAIN.gr_name = 'MAIN'


def start_server():

    def _exit_handler(*a, **k):
        gevent.kill(MAIN, SystemExit)
    sig(signal.SIGTERM, _exit_handler)

    from game import autoenv

    import argparse

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('node', type=str)
    parser.add_argument('--host', default='0.0.0.0', type=str)
    parser.add_argument('--port', default=9999, type=int)
    parser.add_argument('--backdoor-host', default='127.0.0.1', type=str)
    parser.add_argument('--backdoor-port', default=19999, type=int)
    parser.add_argument('--no-backdoor', action='store_true')
    parser.add_argument('--freeplay', action='store_true')
    parser.add_argument('--log', default='INFO')
    parser.add_argument('--logfile', default='')
    parser.add_argument('--gidfile', default='')
    parser.add_argument('--credit-multiplier', type=float, default=1)
    parser.add_argument('--no-counting-flee', action='store_true')
    parser.add_argument('--archive-path', default='')
    parser.add_argument('--interconnect', action='store_true', default=False)
    parser.add_argument('--redis-url', default='redis://localhost:6379')
    parser.add_argument('--discuz-authkey', default='Proton rocks')
    parser.add_argument('--db', default='sqlite:////dev/shm/thb.sqlite3')
    options = parser.parse_args()

    import options as opmodule
    opmodule.options = options

    import db.session
    db.session.init('sqlite://' if options.freeplay else options.db)

    autoenv.init('Server')

    import settings

    utils.logging.init_server(getattr(logging, options.log.upper()), settings.SENTRY_DSN, options.logfile)

    if not options.no_backdoor:
        from gevent.backdoor import BackdoorServer
        gevent.spawn(BackdoorServer((options.backdoor_host, options.backdoor_port)).serve_forever)

    from server.core import Client

    root = logging.getLogger()
    root.info('=' * 20 + settings.VERSION + '=' * 20)
    server = StreamServer((options.host, options.port), Client.serve, None)
    server.serve_forever()


if __name__ == '__main__':
    start_server()
