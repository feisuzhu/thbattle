import pyglet

from pyglet.graphics import *
from pyglet.gl import *

import types
from time import time

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 718

class Control(pyglet.event.EventDispatcher):
    def __init__(self, x=0, y=0, width=100, height=100,
                zindex=0, parent=None, can_focus=False, manual_draw=False,
                *args, **kwargs):
        if parent is None:
            parent = Overlay.cur_overlay
            overlay = parent
        else:
            if parent:
                overlay = parent
                while not isinstance(overlay, Overlay):
                    overlay = overlay.parent
            else:
                overlay = self

        self.__dict__.update({
            'parent': parent,
            'x': x, 'y': y,
            '_w': width, '_h': height,
            'zindex': zindex,
            'can_focus': can_focus,
            'manual_draw': manual_draw,
        })
        self.control_list = []
        self.continuation = None
        self.overlay = overlay
        # control under cursor now, for tracking enter/leave events
        self._control_hit = None
        if parent:
            parent.add_control(self)

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

    def remove_control(self, c):
        self.control_list.remove(c)

    def delete(self):
        self.parent.remove_control(self)

    def controls_frompoint(self, x, y):
        l = []
        for c in self.control_list:
            if c.x <= x <= c.x + c.width and c.y <= y <= c.y + c.height:
                l.append(c)
        return l

    def control_frompoint1(self, x, y):
        l = self.controls_frompoint(x, y)
        # l.sort(key=lambda c: c.zindex, reverse=True)
        l.sort(key=lambda c: c.zindex)
        l.reverse()
        return l[0] if l else None

    def stop_drawing(self):
        if self.continuation:
            self.continuation.close()
            self.continuation = None

    def do_draw(self, dt):
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        self._do_draw(dt)
        glPopMatrix()

    def _do_draw(self, dt):
        if self.continuation:
            try:
                self.continuation.send(dt)
            except StopIteration:
                self.continuation = None
                ''' Animation are supposed to be written like this:
                def the_drawing(dt):
                    for i in range(n_frames):
                        do_the_drawing_step(i, dt)
                        dt = (yield)
                When StopIteration occurs, nothing was done.
                call do_draw again to do the drawing
                '''
                return self._do_draw(dt)

        elif hasattr(self, 'draw'):
            rst = self.draw(dt)
            if type(rst) == types.GeneratorType:
                try:
                    rst.next()
                    self.continuation = rst
                except StopIteration:
                    print 'Stop first'

        else:
            # default behavior
            if not hasattr(self, 'label'):
                from pyglet.text import Label
                self.label = Label(text=self.__class__.__name__,
                                    font_size=10,color=(0,0,0,255),
                                    x=self.width//2, y=self.height//2,
                                    anchor_x='center', anchor_y='center')
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

        #self.draw_subcontrols(dt)

    def draw_subcontrols(self, dt):
        self.control_list.sort(key=lambda c: c.zindex)
        for c in self.control_list:
            if not c.manual_draw:
                c.do_draw(dt)

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
        while not isinstance(c, Overlay):
            ax += c.x
            ay += c.y
            c = c.parent
        return (ax, ay)

class Overlay(Control):
    '''
    Represents current screen
    '''
    class DummyOverlay(object):
        def dispatch_event(*args):
            pass
    cur_overlay = DummyOverlay()
    def __init__(self, *args, **kwargs):
        Control.__init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
                         parent=False)
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

    def draw(self, dt):
        main_window.clear()
        self.draw_subcontrols(dt)

    def switch(self):
        ori = Overlay.cur_overlay
        ori.dispatch_event('on_switchout')
        Overlay.cur_overlay = self
        main_window.set_handlers(self)
        self.dispatch_event('on_switch')
        return ori

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1000, 1000)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED

    def _position_events(self, _type, x, y, *args):
        cap_list = self._capture_events.setdefault(_type, [])
        def dispatch(this, lx, ly):
            '''
            # Every hit control get event

            l = this.controls_frompoint(lx, ly)

            last = set(this._controls_hit)
            now = set(l)
            for c in last - now:
                c.dispatch_event('on_mouse_leave', lx - c.x, ly - c.y)

            for c in now - last:
                c.dispatch_event('on_mouse_enter', lx - c.x, ly - c.y)

            this._controls_hit = l

            if not l:
                if this is not self:
                    this.dispatch_event(_type, lx, ly, *args)
            else:
                for c in l:
                    dispatch(c, lx-c.x, ly-c.y)
            '''

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
        if cap_list:
            con = cap_list[-1]
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

    def _text_events(self, *args):
        if self.current_focus:
            self.current_focus.dispatch_event(*args)

    on_key_press = lambda self, *args: self._text_events('on_key_press', *args)
    on_key_release = lambda self, *args: self._text_events('on_key_release', *args)
    on_text = lambda self, *args: self._text_events('on_text', *args)
    on_text_motion = lambda self, *args: self._text_events('on_text_motion', *args)
    on_text_motion_select = lambda self, *args: self._text_events('on_text_motion_select', *args)

    def dispatch_message(self, args):
        for c in self.control_list:
            self.dispatch_message(self, args)
        self.dispatch_event('on_message', *args)

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
    global main_window, msg_queue, msg_queue_lock
    import threading
    main_window = pyglet.window.Window(
        width=WINDOW_WIDTH, height=WINDOW_HEIGHT, caption='GensouKill')
    msg_queue = []
    msg_queue_lock = threading.RLock()

    # main window setup {{
    glClearColor(1, 1, 1, 1)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_SCISSOR_TEST)
    def_overlay = Overlay()
    def_overlay.name = 'Overlay'
    def_overlay.switch()
    # }} main window setup

    fps = pyglet.clock.ClockDisplay()

    def _mainwindow_loop(dt):
        global msg_queue, msg_queue_lock
        o = Overlay.cur_overlay
        o.do_draw(dt)
        fps.draw()
        #main_window.flip()
        with msg_queue_lock:
            if msg_queue:
                for m in msg_queue:
                    o.dispatch_message(m)
                msg_queue = []
    pyglet.clock.schedule_interval(_mainwindow_loop, 1/60.0)

def message(*args):
    '''
    Send message to UI
    '''
    global msg_queue, msg_queue_lock
    with msg_queue_lock:
        msg_queue.append(args)

if __name__ == '__main__':
    init_gui()
    Control(100, 100, can_focus=True).name = 'Foo'
    Control(150, 150, can_focus=True).name = 'Bar'
    Control(170, 170, can_focus=True).name = 'Youmu'
    '''
    o = Overlay()
    o = o.switch()
    Control(170, 170)
    Control(150, 150)
    Control(100, 100)
    def sss(dt):
        global o
        o = o.switch()'''
    #pyglet.clock.schedule_interval(sss, 1)

    pyglet.app.run()
