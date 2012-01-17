import threading
import pyglet
from client.ui.base import init_gui
from screens import LoadingScreen, LoginScreen

def start_ui():
    init_gui()
    # start a new thread and load,
    # then switch to LoginScreen
    pld, login = LoadingScreen(), LoginScreen()
    LoadingScreen().switch()
    class PreloadThread(threading.Thread):
        def run(self):
            import time
            time.sleep(1)
            self.login.switch()
    plds = PreloadThread()
    plds.login = login
    plds.start()
    pyglet.app.run()
