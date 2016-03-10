# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import gevent
from gevent import monkey
monkey.patch_all()

from gevent.server import StreamServer

import logging

MAIN = gevent.getcurrent()

from gevent import signal as sig
import signal


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
    db.session.init(options.db)

    autoenv.init('Server')

    import settings

    class ServerLogFormatter(logging.Formatter):
        def format(self, rec):

            if rec.exc_info:
                s = []
                s.append('>>>>>>' + '-' * 74)
                s.append(self._format(rec))
                import traceback
                s.append(u''.join(traceback.format_exception(*rec.exc_info)).strip())
                s.append('<<<<<<' + '-' * 74)
                return u'\n'.join(s)
            else:
                return self._format(rec)

        def _format(self, rec):
            from game.autoenv import Game
            import time
            try:
                g = Game.getgame()
            except:
                g = gevent.getcurrent()

            gr_name = getattr(g, 'gr_name', None) or repr(g)
            gr_name = 'MAIN' if g is MAIN else gr_name

            return u'[%s %s %s] %s' % (
                rec.levelname[0],
                time.strftime('%y%m%d %H:%M:%S'),
                gr_name.decode('utf-8'),
                rec.msg % rec.args if isinstance(rec.msg, basestring) else repr((rec.msg, rec.args)),
            )

    fmter = ServerLogFormatter()

    root = logging.getLogger()

    root.setLevel(getattr(logging, options.log.upper()))
    std = logging.StreamHandler(stream=sys.stdout)
    std.setFormatter(fmter)
    root.handlers = []
    root.addHandler(std)

    if options.logfile:
        from logging.handlers import WatchedFileHandler
        filehdlr = WatchedFileHandler(options.logfile)
        filehdlr.setFormatter(fmter)
        root.addHandler(filehdlr)

    if not options.no_backdoor:
        from gevent.backdoor import BackdoorServer
        gevent.spawn(BackdoorServer((options.backdoor_host, options.backdoor_port)).serve_forever)

    from server.core import Client

    root.info('=' * 20 + settings.VERSION + '=' * 20)
    server = StreamServer((options.host, options.port), Client.spawn, None)
    server.serve_forever()


if __name__ == '__main__':
    start_server()
