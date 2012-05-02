# -*- coding: utf-8 -*-
import threading
import pyglet
from client.ui.base import init_gui
from screens import ServerSelectScreen

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
    ServerSelectScreen().switch()
    pyglet.app.run()
