# -*- coding: utf-8 -*-
import threading
from client.ui.base import init_gui, schedule as ui_schedule
from screens import UpdateScreen, ServerSelectScreen
import sys, os

import logging
log = logging.getLogger('UI_Entry')

def start_ui():
    # custom font renderer
    import pyglet
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

    errmsgs = {
        'update_disabled': u'自动更新已被禁止',
        'error': u'更新过程出现错误，您可能无法正常进行游戏！',
    }

    def display_box(msg):
        from client.ui.controls import ConfirmBox
        b = ConfirmBox(msg, parent=us)
        @b.event
        def on_confirm(val):
            sss.switch()

    def update_callback(msg):
        if msg == 'up2date':
            sss.switch()
        elif msg in errmsgs:
            ui_schedule(display_box, errmsgs[msg])
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)

    Executive.call('update', update_callback, lambda *a: ui_schedule(us.update_message, *a))


    # workaround for pyglet's bug
    if sys.platform == 'win32':
        import pyglet.app.win32
        pyglet.app.win32.Win32EventLoop._next_idle_time = None
    pyglet.app.run()
