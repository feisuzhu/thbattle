import threading

import logging, sys

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('__main__')

class MainThread(threading.Thread):
    def run(self):
        from utils import ITIHub,ITIEvent; ITIHub.replace_default()
        
        from game import autoenv
        autoenv.init('Client')
        
        from client.core import Executive
        
        from network import Endpoint
        Endpoint.ENDPOINT_DEBUG = True
        
        Executive.run()
        
MainThread().start()

from client.ui.entry import start_ui
start_ui()

