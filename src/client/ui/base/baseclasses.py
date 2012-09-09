# -*- coding: utf-8 -*-
import pyglet

from pyglet.graphics import *
from pyglet.gl import *

import types
from time import time
from utils import rect_to_dict as r2d, Rect

from functools import partial

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 720

from utils import hook

import logging
log = logging.getLogger('UI_Baseclasses')


import pyglet_extension # just init it

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
        self._clist_inuse = False
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
        if self._clist_inuse:
            self.control_list = self.control_list[:]
            self._clist_inuse = False
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
        l.reverse()
        while l:
            c = l[0]
            rst = c.hit_test(x-c.x, y-c.y)
            if rst:
                return c
            else:
                del l[0]
                continue
        else:
            return None

    def hit_test(self, x, y):
        return True

    def do_draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        rst = self.draw()
        glPopMatrix()

    def draw(self):
        # default behavior
        if not hasattr(self, 'label'):
            '''
            w, h = self.width, self.height
            batch = pyglet.graphics.Batch()
            glColor3f(1,1,1)
            batch.add(4, GL_QUADS, None, ('v2i', (
                0,0, 0,h, w,h, w,0,
            )))
            glColor3f(0,0,0)
            batch.add(
                5, GL_LINE_STRIP, None,
                ('v2i', Rect(0,0,w,h).glLineStripVertices()),
            )

            v = []
            v.extend(Rect(0,   0,   4, 4).glQuadsVertices())
            v.extend(Rect(w-4, 0,   4, 4).glQuadsVertices())
            v.extend(Rect(0,   h-4, 4, 4).glQuadsVertices())
            v.extend(Rect(w-4, h-4, 4, 4).glQuadsVertices())

            batch.add(4*4, GL_QUADS, None, ('v2i', v))
            batch.add(5, GL_LINE_STRIP, None, ('v2i', (
                0,0, 0,10, 10,10, 10,0, 0,0
            )))'''

            from pyglet.text import Label
            if not hasattr(self, '_text'):
                self._text = self.__class__.__name__

            self.label = Label(
                text=self._text,
                font_size=10,color=(0,0,0,255),
                x=self.width//2, y=self.height//2,
                anchor_x='center', anchor_y='center',
            )

        if self._text != self.label.text:
            self.label.text = self._text

        glPushAttrib(GL_POLYGON_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glColor3f(1.0, 1.0, 1.0)
        glRecti(0, 0, self.width, self.height)
        glColor3f(0.0, 0.0, 0.0)
        glRecti(0, 0, 4, 4)
        glRecti(self.width-4, 0, self.width, 4)
        glRecti(0, self.height-4, 4, self.height)
        glRecti(self.width-4, self.height-4, self.width, self.height)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, self.width, self.height)
        glBegin(GL_POLYGON)
        glVertex2f(0,0)
        glVertex2f(0,10)
        glVertex2f(10,10)
        glVertex2f(10, 0)
        glEnd()
        glPopAttrib()

        self.label.draw()
        self.draw_subcontrols()

    def draw_subcontrols(self):
        self.control_list.sort(key=lambda c: c.zindex)
        self._clist_inuse = True
        for c in self.control_list:
            if not c.manual_draw:
                c.do_draw()
        self._clist_inuse = False

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
            (0.0, None, 0.0, 0.0), # (time(), self._control_hit, x, y) LEFT
            (0.0, None, 0.0, 0.0), # MIDDLE
            None,                  # Not used
            (0.0, None, 0.0, 0.0), # RIGHT
        ]
        self.last_mouse_release = [
            None,
            (0.0, None, 0.0, 0.0), # (time(), self._control_hit, x, y) LEFT
            (0.0, None, 0.0, 0.0), # MIDDLE
            None,                  # Not used
            (0.0, None, 0.0, 0.0), # RIGHT
        ]
        self.current_focus = None
        self._capture_events = {}

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
                dispatch(c, lx - c.x, ly - c.y) # TODO: not recursive
                if not c in cap_list: # do not redispatch the same event
                    c.dispatch_event(_type, lx - c.x, ly - c.y, *args)

        # capturing events
        for con in cap_list:
            ax, ay = con.abs_coords()
            con.dispatch_event(_type, x-ax, y-ay, *args)
        dispatch(self, x, y)

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
        if cr[0]-lr[0] < 0.2: # time limit
            if abs(cr[2] - lr[2]) + abs(cr[3] - lr[3]) < 4: # shift limit
                if cr[1] == lr[1]: # Control limit
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

    on_key_press = lambda self, *args: self._text_events('on_key_press', *args)
    on_key_release = lambda self, *args: self._text_events('on_key_release', *args)
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
    global main_window, sched_queue, sched_queue_lock, current_time, fps_limit
    import threading

    config = pyglet.gl.Config(
        double_buffer = True,
        buffer_size = 32,
        aux_buffers = 0,
        sample_buffers = 0,
        samples = 0,
        red_size = 8,
        green_size = 8,
        blue_size = 8,
        alpha_size = 8,
        depth_size = 0,
        stencil_size = 0,
        accum_red_size = 0,
        accum_green_size = 0,
        accum_blue_size = 0,
        accum_alpha_size = 0,
    )

    main_window = pyglet.window.Window(
        width=WINDOW_WIDTH, height=WINDOW_HEIGHT, caption=u'东方符斗祭',
        config=config,
    )
    sched_queue = []
    sched_queue_lock = threading.RLock()

    # main window setup {{
    glClearColor(1, 1, 1, 1)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    #glEnable(GL_SCISSOR_TEST)
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
        t = time()
        dt = t - current_time
        current_time = t
        Overlay.cur_overlay.do_draw()
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
        global sched_queue, sched_queue_lock
        if not sched_queue: return
        with sched_queue_lock:
            for func in sched_queue:
                func()
            sched_queue = []
    pyglet.clock.schedule_interval(_dispatch_msg, delay)

    # if gc runs in the game thread,
    # thing related to graphic will be recycled,
    # thus freeing OpenGL resource from THE OTHER thread,
    # whoop, segfaults.
    # will this is perhaps naive approach
    import gc
    gc.disable()
    pyglet.clock.schedule_interval_soft(lambda dt: gc.collect(0), 1)
    pyglet.clock.schedule_interval_soft(lambda dt: gc.collect(2), 7)

def schedule(func, *args, **kwargs):
    global sched_queue, sched_queue_lock
    with sched_queue_lock:
        sched_queue.append(partial(func, *args, **kwargs))

def _msg(args):
    Overlay.cur_overlay.dispatch_message(args)

def message(*args):
    '''
    Send message to UI
    '''
    schedule(_msg, args)
