# -*- coding: utf-8 -*-
import threading
import logging, sys

class Tee(object):
    def __init__(self):
        self.logfile = f = open('client_log.txt', 'a')
        import datetime
        f.write(
            '\n' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") +
            '\n==============================================\n'
        )

    def write(self, v):
        sys.__stdout__.write(v)
        self.logfile.write(v)

sys.stderr = sys.stdout = Tee()

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger('__main__')

_sync_evt = threading.Event()

class MainThread(threading.Thread):
    def run(self):
        import utils; utils.patch_gevent_hub()

        from gevent import monkey
        monkey.patch_socket()

        from game import autoenv
        autoenv.init('Client')

        from client.core import Executive

        # for dbg
        '''
        from gevent import signal as gsig
        import signal
        def print_stack():
            game = Executive.gm_greenlet.game
            import traceback
            traceback.print_stack(game.gr_frame)
        gsig(signal.SIGUSR1, print_stack)
        # -------
        '''

        _sync_evt.set()
        Executive.run()

mt = MainThread()
mt.start()

_sync_evt.wait()
del _sync_evt

from client.ui.entry import start_ui

try:
    start_ui()
except:
    import traceback
    traceback.print_exc()
    import pyglet
    pyglet.app.exit()

from client.core import Executive
Executive.call('app_exit')
