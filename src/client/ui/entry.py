import threading
import pyglet
from client.ui.base import init_gui
from screens import LoadingScreen, ServerSelectScreen

def start_ui():
    init_gui()
    # start a new thread and load,
    # then switch to LoginScreen
    pld, svrsel = LoadingScreen(), ServerSelectScreen()
    LoadingScreen().switch()
    class PreloadThread(threading.Thread):
        def run(self):
            import time
            #time.sleep(1)
            self.svrsel.switch()
    plds = PreloadThread()
    plds.svrsel = svrsel
    plds.start()
    pyglet.app.run()
