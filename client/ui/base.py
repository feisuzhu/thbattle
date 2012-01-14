import pyglet

from pyglet.graphics import *
from pyglet.gl import *
from functools import partial

import types

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 720

class Control(pyglet.event.EventDispatcher):
    def __init__(self, x=0, y=0, width=100, height=100, zindex=0, parent=None, can_focus=False):
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
            'width': width, 'height': height,
            'zindex': zindex,
            'can_focus': can_focus, #TODO
        })
        self.control_list = []
        self.continuation = None
        self.overlay = overlay
        self._control_hit = None # control under cursor now, for tracking enter/leave events
        if parent:
            parent.add_control(self)
    
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
    
    def do_draw(self, dt):
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
                return self.do_draw(dt)
                
        if hasattr(self, 'draw'):
            rst = self.draw(dt)
            if type(rst) == types.GeneratorType:
                self.continuation = rst
                rst.next()
        else:
            # default behavior
            if not hasattr(self, 'label'):
                self.label = pyglet.text.Label(text=self.__class__.__name__,
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
        
        self._draw_subcontrols(dt)
    
    def _draw_subcontrols(self, dt):
        self.control_list.sort(key=lambda c: c.zindex)
        for c in self.control_list:
            glPushMatrix()
            glTranslatef(c.x, c.y, 0)
            c.do_draw(dt)
            glPopMatrix()
    def on_mouse_enter(self, x, y):
        print '%s Enter! %d %d' % (self.name, x, y)
    def on_mouse_leave(self, x, y):
        print '%s Leave! %d %d' % (self.name, x, y)
        
    def setfocus(self):
        c = self.parent
        if c:
            pass
            
        
class Overlay(Control):
    '''
    Represents current screen
    '''
    cur_overlay = None
    def __init__(self, **kwargs):
        Control.__init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, parent=False)
        self.__dict__.update(kwargs)
    
    def draw(self, dt):
        main_window.clear()
    
    def switch(self):
        ori = Overlay.cur_overlay
        Overlay.cur_overlay = self
        main_window.set_handlers(self)
        return ori
    
    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1000, 1000)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED
    
    def _position_events(self, type, x, y, *args):
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
                    this.dispatch_event(type, lx, ly, *args)
            else:
                for c in l:
                    dispatch(c, lx-c.x, ly-c.y)
            '''
            
            # Top most control get event
            c = this.control_frompoint1(lx, ly)
            lc = this._control_hit
            if c != lc:
                if lc:
                    lc.dispatch_event('on_mouse_leave', lx - lc.x, ly - lc.y)
                if c:
                    c.dispatch_event('on_mouse_enter', lx - c.x, ly - c.y)
            this._control_hit = c
            
            if not c:
                if this is not self:
                    this.dispatch_event(type, lx, ly, *args)
            else:
                dispatch(c, lx - c.x, ly - c.y) # TODO: not recursive
            
        dispatch(self, x, y)
    
    on_mouse_motion = lambda self, *args: self._position_events('on_mouse_motion', *args)
    on_mouse_press = partial(_position_events, 'on_mouse_press')
    on_mouse_drag = partial(_position_events, 'on_mouse_drag')
    on_mouse_release = partial(_position_events, 'on_mouse_release')
    on_mouse_scroll = partial(_position_events, 'on_mouse_scroll')

Control.register_event_type('on_mouse_motion')
Control.register_event_type('on_mouse_press')
Control.register_event_type('on_mouse_drag')
Control.register_event_type('on_mouse_release')
Control.register_event_type('on_mouse_scroll')
Control.register_event_type('on_mouse_enter')
Control.register_event_type('on_mouse_leave')




def init_gui():
    global main_window
    main_window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, caption='GensouKill')
    
    # main window setup {{
    glClearColor(1, 1, 1, 1)
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    def_overlay = Overlay()
    def_overlay.name = 'Overlay'
    def_overlay.switch()
    # }} main window setup
    
    fps = pyglet.clock.ClockDisplay()
    
    def _mainwindow_draw(dt):
        Overlay.cur_overlay.do_draw(dt)
        fps.draw()
        #main_window.flip()
    pyglet.clock.schedule_interval(_mainwindow_draw, 1/40.0)

if __name__ == '__main__':
    init_gui()
    Control(100, 100).name = 'Foo'
    Control(150, 150).name = 'Bar'
    Control(170, 170).name = 'Youmu'
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