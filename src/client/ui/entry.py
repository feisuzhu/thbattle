# -*- coding: utf-8 -*-
import threading
import sys, os

from utils import hook

import logging
log = logging.getLogger('UI_Entry')

def start_ui():
    # ATI workarounds
    import pyglet
    from pyglet import gl
    @hook(gl)
    def glDrawArrays(ori, *a, **k):
        from pyglet.gl import glBegin, glEnd, GL_QUADS
        glBegin(GL_QUADS)
        glEnd()
        return ori(*a, **k)

    # ---------------

    from client.ui.base import init_gui, ui_schedule, ui_message

    init_gui()

    # This forces all game resources to initialize,
    # else they will be imported firstly by GameManager,
    # then resources will be loaded at a different thread,
    # resulting white planes.
    # UPDATE: no more threading now, but retain notice above.
    import gamepack

    # custom errcheck
    import pyglet.gl.lib as gllib
    orig_errcheck = gllib.errcheck

    import ctypes
    def my_errcheck(result, func, arguments):
        from pyglet import gl
        error = gl.glGetError()
        if error and error != 1286:
            # HACK: The 1286(INVALID_FRAMEBUFFER_OPERATION) error again!
            # This time I DIDN'T EVEN USE FBO! ATI!!
            msg = ctypes.cast(gl.gluErrorString(error), ctypes.c_char_p).value
            raise gl.GLException((error, msg))
        return result

    gllib.errcheck = my_errcheck
    # ------------------------------------

    from screens import UpdateScreen, ServerSelectScreen

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
        # executes in logic thread
        # well, intented to be
        # ui and logic now run in the same thread.

        from options import options
        if msg == 'up2date':
            ui_schedule(sss.switch)
        elif msg == 'update_disabled' and options.fastjoin:
            import gevent
            def func():
                gevent.sleep(0.3)
                ui_schedule(sss.switch)
                gevent.sleep(0.3)
                Executive.call('connect_server', ui_message, ('127.0.0.1', 9999), ui_message)
                gevent.sleep(0.3)
                Executive.call('auth', ui_message, ['Proton1', 'abcde'])
                gevent.sleep(0.3)
                Executive.call('quick_start_game', ui_message, 'THBattle')
                gevent.sleep(0.3)
                Executive.call('get_ready', ui_message, [])

            gevent.spawn(func)
                
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
