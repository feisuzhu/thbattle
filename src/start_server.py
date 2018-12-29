# -*- coding: utf-8 -*-

# -- prioritized --
from gevent import monkey
monkey.patch_all()

# -- stdlib --
import logging
import signal
import sys
import urllib.parse

# -- third party --
from gevent import signal as sig
from gevent.server import StreamServer
import gevent

# -- own --
import utils
import utils.log

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
    parser.add_argument('--listen', default='tcp://0.0.0.0:9999', type=str)
    parser.add_argument('--backdoor', default='tcp://127.0.0.1:19999', type=str)
    parser.add_argument('--log', default='file:///dev/shm/thb.log?level=INFO')
    parser.add_argument('--archive-path', default='file:///dev/shm/thb-archive')
    parser.add_argument('--backend', default='http://uid:pass@localhost/graphql')
    parser.add_argument('--interconnect', default='ws://uid:pass@localhost/interconnect')
    options = parser.parse_args()

    autoenv.init('Server')

    import settings

    log = urllib.parse.urlparse(options.log)
    assert log.scheme == 'file'
    args = dict(urllib.parse.parse_qsl(log.query))
    utils.log.init_server(args.get('level', 'INFO').upper(), settings.SENTRY_DSN, settings.VERSION, log.path)

    if not options.no_backdoor:
        from gevent.backdoor import BackdoorServer
        a = urllib.parse.urlparse(options.backdoor)
        gevent.spawn(BackdoorServer((a.hostname, a.port)).serve_forever)

    root = logging.getLogger()
    root.info('=' * 20 + settings.VERSION + '=' * 20)

    from server.core import Core

    core = Core(
        node=options.node,
        interconnect=options.interconnect,
        archive_path=options.archive_path,
        backend=options.backend,
    )

    def serve(sock, addr):
        from endpoint import Endpoint
        from server.endpoint import Client

        ep = Endpoint(sock, addr)
        cli = Client(core, ep)
        cli.serve()

    a = urllib.parse.urlparse(options.listen)
    server = StreamServer((a.hostname, options.port), serve, None)
    server.serve_forever()


if __name__ == '__main__':
    start_server()
