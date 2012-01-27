import threading
import pyglet
from client.ui.base import init_gui
from screens import LoadingScreen, ServerSelectScreen

import logging
log = logging.getLogger('UI_Entry')

def start_ui():
    init_gui()
    # start a new thread and load,
    # then switch to LoginScreen
    pld, svrsel = LoadingScreen(), ServerSelectScreen()
    LoadingScreen().switch()
    class PreloadThread(threading.Thread):
        def run(self):
            self.svrsel.switch()
    plds = PreloadThread()
    plds.svrsel = svrsel
    plds.start()
    # This forces all game resources to initialize,
    # else they will be imported firstly by GameManager,
    # then resources will be loaded at a different thread,
    # resulting white planes.
    import gamepack
    pyglet.app.run()
