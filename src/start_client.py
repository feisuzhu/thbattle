# -*- coding: utf-8 -*-
import threading
import logging, sys

reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

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
        self.logfile.write(v.encode('utf-8'))

sys.stderr = sys.stdout = Tee()

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger('__main__')

_sync_evt = threading.Event()

class MainThread(threading.Thread):
    def run(self):
        import utils; utils.patch_gevent_hub()

        import gevent
        from gevent import monkey
        monkey.patch_socket()

        # ipv4 only, dns retry
        from gevent import socket, dns
        origGetAddrInfo = socket.getaddrinfo

        def getAddrInfoWrapper(host, port, family=0, socktype=0, proto=0, flags=0):
            while True:
                try:
                    return origGetAddrInfo(host, port, socket.AF_INET, socktype, proto, flags)
                except dns.DNSError as e:
                    if not e.errno == 2: # server fail thing
                        raise
                gevent.sleep(0.15)

        # replace the original socket.getaddrinfo by our version
        socket.getaddrinfo = getAddrInfoWrapper
        # -----------------------------------------

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
