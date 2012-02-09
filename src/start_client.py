import threading
import logging, sys

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('__main__')

from gevent import monkey
monkey.patch_all(thread=False, time=False)

class MainThread(threading.Thread):
    def run(self):
        from utils import ITIHub; ITIHub.replace_default()

        from game import autoenv
        autoenv.init('Client')

        from client.core import Executive

        from network import Endpoint
        Endpoint.ENDPOINT_DEBUG = True

        Executive.run()

mt = MainThread()
mt.start()

from client.ui.entry import start_ui
start_ui()

from client.core import Executive
Executive.call('app_exit')
