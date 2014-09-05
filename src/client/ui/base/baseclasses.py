# -*- coding: utf-8 -*-
from collections import defaultdict

import pyglet

from pyglet.gl import glBlendFunc, glClearColor, glEnable, glLoadIdentity, glMatrixMode, glOrtho
from pyglet.gl import glPolygonMode, glPopMatrix, glPushMatrix, glTranslatef, glViewport
from pyglet.gl import GL_BACK, GL_BLEND, GL_FILL, GL_FRONT, GL_LINE, GL_MODELVIEW
from pyglet.gl import GL_ONE_MINUS_SRC_ALPHA, GL_PROJECTION, GL_SRC_ALPHA

from time import time

from functools import partial

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 720

main_window = None
sched_queue = []

from utils import hook

import logging
log = logging.getLogger('UI_Baseclasses')


class Control(pyglet.event.EventDispatcher):
    def __init__(self, x=0, y=0, width=0, height=0,
                zindex=0, parent=None, can_focus=False, manual_draw=False,
                *args, **kwargs):

        self.__dict__.update({
            'parent': parent,
            'x': x, 'y': y,
            '_w': width, '_h': height,
            'zindex': zindex,
            'can_focus': can_focus,
            'manual_draw': manual_draw,
        })
        self.__dict__.update(kwargs)
        self.control_list = []
        # control under cursor now, for tracking enter/leave events
        self._control_hit = None
        if parent:
            parent.add_control(self)
        else:
            self.parent = parent
            self.overlay = False

    def _set_w(self, v):
        self._w = v
        self.dispatch_event('on_resize', self._w, self._h)

    def _get_w(self):
        return self._w

    width = property(_get_w, _set_w)

    def _set_h(self, v):
        self._h = v
        self.dispatch_event('on_resize', self._w, self._h)

    def _get_h(self):
        return self._h

    height = property(_get_h, _set_h)

    def add_control(self, c):
        self.control_list.append(c)
        c.parent = self
        c.overlay = self if isinstance(self, Overlay) else self.overlay

    def remove_control(self, c):
        self.control_list.remove(c)
        c.parent = None
        c.overlay = None

    def delete(self):
        if self.parent:
            self.parent.remove_control(self)

    def controls_frompoint(self, x, y):
        l = []
        for c in self.control_list:
            if c.x <= x <= c.x + c.width and c.y <= y <= c.y + c.height:
                if c.hit_test(x-c.x, y-c.y):
                    l.append(c)
        return l

    def control_frompoint1(self, x, y):
        l = self.controls_frompoint(x, y)
        # l.sort(key=lambda c: c.zindex, reverse=True)
        l.sort(key=lambda c: c.zindex)
        while l:
            c = l[-1]
            rst = c.hit_test(x-c.x, y-c.y)
            if rst:
                return c
            else:
                del l[-1]
                continue
        else:
            return None

    def control_frompoint1_recursive(self, x, y):
        c = self
        while True:
            c1 = c.control_frompoint1(x, y)
            if not c1: return c
            x -= c1.x; y -= c1.y; c = c1

    def hit_test(self, x, y):
        return True

    @staticmethod
    def batch_draw(l):
        glPushMatrix()
        for c in l:
            glLoadIdentity()
            x, y = c.abs_coords()
            glTranslatef(x, y, 0)
            c.draw()

        glPopMatrix()

    def draw(self):
        # default behaviors
        self.draw_subcontrols()

    @staticmethod
    def do_draw(cl):
        cl.sort(key=lambda c: (c.zindex, c.batch_draw))
        cl = [c for c in cl if not c.manual_draw]
        if not cl: return

        f = cl[0].batch_draw
        commit = []
        for c in cl:
            if c.batch_draw == f:
                commit.append(c)
            else:
                f(commit)
                commit = [c]
                f = c.batch_draw

        if commit: f(commit)

    def draw_subcontrols(self):
        self.do_draw(self.control_list)

    def set_focus(self):
        if not self.can_focus: return
        o = self.parent
        while not isinstance(o, Overlay):
            o = o.parent

        if o:
            if o.current_focus != self:
                if o.current_focus:
                    o.current_focus.dispatch_event('on_lostfocus')
                self.dispatch_event('on_focus')
                o.current_focus = self

    def set_capture(self, *evts):
        o = self.overlay
        for e in evts:
            o._capture_events.setdefault(e, []).append(self)

    def release_capture(self, *evts):
        o = self.overlay
        for e in evts:
            l = o._capture_events.get(e)
            if l:
                l.remove(self)

    def abs_coords(self):
        c, ax, ay = self, 0.0, 0.0
        while c and not isinstance(c, Overlay):
            ax += c.x
            ay += c.y
            c = c.parent
        return (ax, ay)

    def migrate_to(self, new_parent):
        if self in new_parent.control_list:
            return

        ax, ay = self.abs_coords()
        npax, npay = new_parent.abs_coords()
        self.delete()
        new_parent.add_control(self)
        self.x, self.y = ax-npax, ay-npay

    def on_message(self, *args):
        '''Do nothing'''
        pass

    xy = property(lambda self: (self.x, self.y))


class Overlay(Control):
    '''
    Represents current screen
    FIXME: Should be called Scene
    '''
    class DummyOverlay(object):
        def dispatch_event(*args):
            pass

    cur_overlay = DummyOverlay()

    def __init__(self, *args, **kwargs):
        Control.__init__(
            self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, parent=False
        )
        self.__dict__.update(kwargs)
        self.last_mouse_press = [  # WONTFIX: Button combinations not supported.
            None,
            (0.0, None, 0.0, 0.0),  # (time(), self._control_hit, x, y) LEFT
            (0.0, None, 0.0, 0.0),  # MIDDLE
            None,                   # Not used
            (0.0, None, 0.0, 0.0),  # RIGHT
        ]
        self.last_mouse_release = [
            None,
            (0.0, None, 0.0, 0.0),  # (time(), self._control_hit, x, y) LEFT
            (0.0, None, 0.0, 0.0),  # MIDDLE
            None,                   # Not used
            (0.0, None, 0.0, 0.0),  # RIGHT
        ]
        self.current_focus = None
        self._capture_events = {}

        self.key_state = defaultdict(bool)

    def draw(self):
        main_window.clear()
        self.draw_subcontrols()

    def switch(self):
        ori = Overlay.cur_overlay
        ori.dispatch_event('on_switchout')
        Overlay.cur_overlay = self
        main_window.set_handlers(self)
        self.dispatch_event('on_switch')

        # HACK
        import gc
        gc.collect()
        # -----

        return ori

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1000, 1000)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED

    def _position_events(self, _type, x, y, *args):
        cap_list = self._capture_events.setdefault(_type, [])[:]

        def dispatch(this, lx, ly):
            # Top most control get event
            c = this.control_frompoint1(lx, ly)
            lc = this._control_hit
            if c != lc:
                while lc:
                    lc.dispatch_event('on_mouse_leave', lx - lc.x, ly - lc.y)
                    lc._control_hit, lc = None, lc._control_hit
                if c:
                    c.dispatch_event('on_mouse_enter', lx - c.x, ly - c.y)
            this._control_hit = c

            if not c:
                # Now 'this' has no subcontrols hit, so 'this' got this event
                # TODO: if 'this' don't handle it, its parent should handle.
                if this is not self:
                    if _type == 'on_mouse_press':
                        this.set_focus()
            else:
                if dispatch(c, lx - c.x, ly - c.y):  # TODO: not recursive
                    return True
                if c not in cap_list:  # do not redispatch the same event
                    return c.dispatch_event(_type, lx - c.x, ly - c.y, *args)

        # capturing events
        for con in cap_list:
            ax, ay = con.abs_coords()
            if con.dispatch_event(_type, x-ax, y-ay, *args):
                return True

        return dispatch(self, x, y)

    def on_mouse_press(self, x, y, button, modifier):
        self.last_mouse_press[button] = (time(), self._control_hit, x, y)
        self._position_events('on_mouse_press', x, y, button, modifier)

    def on_mouse_release(self, x, y, button, modifier):
        lp = self.last_mouse_press[button]
        lr = self.last_mouse_release[button]
        cr = (time(), self._control_hit, x, y)
        self.last_mouse_release[button] = cr
        self._position_events('on_mouse_release', x, y, button, modifier)
        # single click
        if cr[1] == lp[1]:
            self._position_events('on_mouse_click', x, y, button, modifier)

        # double click
        if cr[0]-lr[0] < 0.2:  # time limit
            if abs(cr[2] - lr[2]) + abs(cr[3] - lr[3]) < 4:  # shift limit
                if cr[1] == lr[1]:  # Control limit
                    self._position_events('on_mouse_dblclick', x, y, button, modifier)

    on_mouse_motion = lambda self, *args: self._position_events('on_mouse_motion', *args)
    on_mouse_drag = lambda self, *args: self._position_events('on_mouse_drag', *args)
    on_mouse_scroll = lambda self, *args: self._position_events('on_mouse_scroll', *args)

    def _text_events(self, _type, *args):
        cap_list = self._capture_events.setdefault(_type, [])
        if cap_list:
            con = cap_list[-1]
            con.dispatch_event(_type, *args)
        if self.current_focus:
            self.current_focus.dispatch_event(_type, *args)

    def on_key_press(self, symbol, modifiers):
        self.key_state[symbol] = True
        return self._text_events('on_key_press', symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.key_state[symbol] = False
        return self._text_events('on_key_release', symbol, modifiers)

    on_text = lambda self, *args: self._text_events('on_text', *args)
    on_text_motion = lambda self, *args: self._text_events('on_text_motion', *args)
    on_text_motion_select = lambda self, *args: self._text_events('on_text_motion_select', *args)

    def dispatch_message(self, args):
        l = [self]
        while l:
            c = l.pop(0)
            c.dispatch_event('on_message', *args)
            l.extend(c.control_list)

    def on_message(self, _type, *args):
        if _type == 'app_exit':
            pyglet.app.exit()

Control.register_event_type('on_key_press')
Control.register_event_type('on_key_release')
Control.register_event_type('on_text')
Control.register_event_type('on_text_motion')
Control.register_event_type('on_text_motion_select')
Control.register_event_type('on_mouse_motion')
Control.register_event_type('on_mouse_press')
Control.register_event_type('on_mouse_drag')
Control.register_event_type('on_mouse_release')
Control.register_event_type('on_mouse_scroll')
Control.register_event_type('on_mouse_enter')
Control.register_event_type('on_mouse_leave')
Control.register_event_type('on_mouse_click')
Control.register_event_type('on_mouse_dblclick')
Control.register_event_type('on_focus')
Control.register_event_type('on_lostfocus')
Control.register_event_type('on_message')
Control.register_event_type('on_resize')

Overlay.register_event_type('on_switch')
Overlay.register_event_type('on_switchout')


def init_gui():
    global main_window, sched_queue, current_time, fps_limit

    config = pyglet.gl.Config(
        double_buffer=True,
        buffer_size=32,
        aux_buffers=0,
        sample_buffers=0,
        samples=0,
        red_size=8,
        green_size=8,
        blue_size=8,
        alpha_size=8,
        depth_size=0,
        stencil_size=0,
        accum_red_size=0,
        accum_green_size=0,
        accum_blue_size=0,
        accum_alpha_size=0,
    )

    main_window = pyglet.window.Window(
        width=WINDOW_WIDTH, height=WINDOW_HEIGHT, caption=u'东方符斗祭',
        config=config, visible=False
    )
    sched_queue = []

    from pyglet.gl import gl_info
    vendor = gl_info.get_vendor().lower()
    if 'amd' in vendor or 'ati' in vendor:
        pyglet.options['graphics_vbo'] = False  # AMD: Do you have QA team for your OpenGL driver ????
        from pyglet.graphics import vertexbuffer
        assert not vertexbuffer._enable_vbo

    # custom font renderer
    from .font import AncientPixFont
    pyglet.font._font_class = AncientPixFont

    # main window setup {{
    glClearColor(1, 1, 1, 1)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # glEnable(GL_SCISSOR_TEST)
    glPolygonMode(GL_FRONT, GL_FILL)
    glPolygonMode(GL_BACK, GL_LINE)

    def_overlay = Overlay()
    def_overlay.name = 'Overlay'
    def_overlay.switch()
    # }} main window setup

    fps = pyglet.clock.ClockDisplay()
    fps_limit = 60
    delay = 1. / fps_limit
    current_time = time()

    @main_window.event
    def on_draw():
        global current_time
        current_time = time()
        Overlay.cur_overlay.draw()
        fps.draw()

    @main_window.event
    def on_close():
        # HACK: suppress exceptions,
        # dont want to explain....
        pyglet.clock.tick = lambda a: 0.0
        pyglet.app.exit()

    @hook(main_window)
    def on_key_press(ori, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            return pyglet.event.EVENT_HANDLED
        return ori(symbol, modifiers)

    def _dispatch_msg(dt):
        global sched_queue
        import gevent

        # give logics a chance to run
        gevent.sleep(0)

        if not sched_queue: return

        for func in sched_queue:
            func()

        sched_queue = []

    pyglet.clock.schedule_interval(_dispatch_msg, delay)


def ui_schedule(func, *args, **kwargs):
    global sched_queue
    sched_queue.append(partial(func, *args, **kwargs))


def process_msg(args):
    Overlay.cur_overlay.dispatch_message(args)


def ui_message(*args):
    '''
    Send message to UI
    '''
    ui_schedule(process_msg, args)
