# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())


def start_client():
    import ctypes
    try:
        ctypes.cdll.avbin  # force avbin load
    except:
        pass

    import logging
    import os
    import argparse
    import crashreport

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--testing', action='store_true')
    parser.add_argument('--no-update', action='store_true')
    parser.add_argument('--with-gl-errcheck', action='store_true')
    parser.add_argument('--freeplay', action='store_true')
    parser.add_argument('--fastjoin', action='store_true')
    parser.add_argument('--dump-gameobj', action='store_true')
    parser.add_argument('--log', default='INFO')
    parser.add_argument('--color-log', action='store_true')
    parser.add_argument('--no-crashreport', action='store_true')
    parser.add_argument('--show-hidden-modes', action='store_true')

    options = parser.parse_args()

    import options as opmodule
    opmodule.options = options
    IS_PROTON = hasattr(os, 'uname') and os.uname()[:2] == ('Linux', 'Proton')

    crashreport.install_tee(options.log.upper())

    if IS_PROTON or options.color_log:
        from colorlog import ColoredFormatter

        formatter = ColoredFormatter(
            "%(log_color)s%(message)s%(reset)s",
            log_colors={
                'CRITICAL': 'bold_red',
                'ERROR': 'red',
                'WARNING': 'yellow',
                'INFO': 'green',
                'DEBUG': 'blue',
            }
        )

        logging.getLogger().handlers[0].setFormatter(formatter)

    log = logging.getLogger('start_client')

    # gevent: do not patch dns, they fail on windows
    # monkey.patch_socket(dns=False) won't work since
    # socket.create_connection internally references
    # gevents' getaddrinfo
    import socket
    from gevent import socket as gsock

    if False:
        gsock.getaddrinfo = socket.getaddrinfo
        gsock.gethostbyname = socket.gethostbyname

        # HACK: resolve domain in parallel
        import threading

        class ResolveIt(threading.Thread):
            def __init__(self, host):
                threading.Thread.__init__(self)
                self.host = host

            def run(self):
                host = self.host
                socket.getaddrinfo(host, 80)
                socket.gethostbyname(host)

        domains = [
            'www.thbattle.net',
            'update.thbattle.net',
            'cngame.thbattle.net',
        ]
        for host in domains:
            thread = ResolveIt(host)
            thread.daemon = True
            thread.start()

    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_os()

    from game import autoenv
    autoenv.init('Client')

    import pyglet

    pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')
    pyglet.options['shadow_window'] = False

    if not options.with_gl_errcheck:
        pyglet.options['debug_gl'] = False

    if sys.platform == 'win32':
        from pyglet.media.drivers.directsound import DirectSoundAudioPlayer
        DirectSoundAudioPlayer._buffer_size = 44800 * 2
        DirectSoundAudioPlayer._update_buffer_size = 44800 * 2 // 8

    if sys.platform.startswith('linux') and options.dump_gameobj:
        import atexit
        import game
        atexit.register(game.GameObjectMeta._dump_gameobject_hierarchy)
        atexit.register(game.EventHandler._dump_eh_dependency_graph)

    from client.ui.entry import start_ui

    try:
        start_ui()
    except KeyboardInterrupt:
        import pyglet
        pyglet.app.exit()
        raise
    except:
        import pyglet
        pyglet.app.exit()

        if options.fastjoin:
            import pdb
            pdb.post_mortem()

        if not options.no_crashreport:
            log.error(u'游戏崩溃，正在报告bug，请稍等下……')
            from crashreport import do_crashreport
            do_crashreport()

        raise


if __name__ == '__main__':
    start_client()
