# -*- coding: utf-8 -*-
import threading
import pyglet
from client.ui.base import init_gui, schedule as ui_schedule
from screens import UpdateScreen, ServerSelectScreen

import logging
log = logging.getLogger('UI_Entry')

def start_ui():
    # custom font renderer
    from .base.font import AncientPixFont
    pyglet.font._font_class = AncientPixFont

    init_gui()
    # This forces all game resources to initialize,
    # else they will be imported firstly by GameManager,
    # then resources will be loaded at a different thread,
    # resulting white planes.
    import gamepack
    us = UpdateScreen()
    us.switch()
    from client.core import Executive
    sss = ServerSelectScreen()

    def update_callback(msg):
        print msg
        if msg in ('up2date', 'update_disabled', 'error'):
            sss.switch()
        else:
            import sys, os
            os.execv(sys.executable, [sys.executable] + sys.argv)

    Executive.call('update', update_callback, lambda *a: ui_schedule(us.update_message, *a))

    pyglet.app.run()
