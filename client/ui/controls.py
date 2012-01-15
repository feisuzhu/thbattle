# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from base import Control
from utils.geometry import Rect

class Button(Control):
    NORMAL=0
    HOVER=1
    PRESSED=2
    DISABLED=3
    
    def __init__(self, caption='Button', font_name='Arial', font_size=9, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.caption = caption
        self.font_name = font_name
        self.font_size = font_size
        self.state = Button.NORMAL
        self.label = pyglet.text.Label(caption, font_name, font_size,
                                       color=(0,0,0,255),
                                       x=self.width//2, y=self.height//2,
                                       anchor_x='center', anchor_y='center')
        Control.__init__(self, *args, **kwargs)
        self.color_now = (0.0, 0.0, 0.0)
    
    def draw(self, dt):
        srccolor = self.color_now
        dstcolor = (
            (0.8, 0.8, 0.8),
            (0.5, 0.5, 0.5),
            (0.2, 0.2, 0.2),
            (1.0, 0.2, 0.2),
        )[self.state]
        anim_time = 0.1
        cur_time = 0.0
        while anim_time - cur_time > 0:
            cur_time += dt
            delta = [(dst - cur)*(dt/anim_time) for cur, dst in zip(srccolor, dstcolor)]
            self.color_now = [
                (now+dc if (dst-now-dc)*(dst-now)>0 else dst)
                for now, dst, dc in zip(self.color_now, dstcolor, delta)
            ]
            glPushAttrib(GL_POLYGON_BIT)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glColor3f(*self.color_now)
            glRecti(0, 0, self.width, self.height)
            glPopAttrib()
            self.label.draw()
            #self.draw_subcontrols()
            dt = (yield)
    
    def on_mouse_enter(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.HOVER
            self.stop_drawing()
        
    def on_mouse_leave(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.NORMAL
            self.stop_drawing()
    
    def on_mouse_press(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.PRESSED
                self.stop_drawing()
    
    def on_mouse_release(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.HOVER
                self.stop_drawing()
    
    def on_mouse_click(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            self.dispatch_event('on_click')

Button.register_event_type('on_click')

class Dialog(Control):
    '''
    Dialog, can move
    '''
    next_zindex = 1
    def __init__(self, caption='Dialog', *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.zindex = Dialog.next_zindex
        Dialog.next_zindex += 1
        self.label = pyglet.text.Label(caption, 'Arial', 9,
                               color=(0,0,0,255),
                               x=self.width//2, y=self.height-8,
                               anchor_x='center', anchor_y='center')
        self.btn_close = Button(caption=u'', parent=self, font_size=12,
                                x=self.width-20, y=self.height-19,
                                width=19, height=19, manual_draw=True)
        self.dragging = False
        @self.btn_close.event
        def on_click():
            self.close()
    
    def draw(self, dt):
        w, h = self.width, self.height
        ax, ay = self.abs_coords()
        ax, ay = int(ax), int(ay)
        
        ob = (GLint*4)()
        glGetIntegerv(GL_SCISSOR_BOX, ob)
        ob = list(ob)
        nb = Rect(*ob).intersect(Rect(ax, ay, w, h))
        if nb:
            glScissor(nb.x, nb.y, nb.width, nb.height)
            glClear(GL_COLOR_BUFFER_BIT)
            glScissor(nb.x, nb.y, nb.width, nb.height-20)
            self.draw_subcontrols(dt)
            glScissor(*ob)
            
        glColor3f(0, 0, 0)
        self.label.draw()
        self.btn_close.do_draw(dt)
        glColor3f(0, 0, 0)
        glPushAttrib(GL_POLYGON_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, w, h)
        graphics.draw(5, GL_LINE_STRIP,('v2i', (
            0, h-20,
            w, h-20,
            w-20, h,
            w-20, h-20,
            w, h,
        )))
        glPopAttrib()
    
    def on_mouse_press(self, x, y, button, modifier):
        w, h = self.width, self.height
        self.zindex = Dialog.next_zindex
        Dialog.next_zindex += 1
        if button == mouse.LEFT and h-20 <= y <= h and x <= w-20:
            self.set_capture('on_mouse_drag', 'on_mouse_release')
            self.dragging = True
    
    def on_mouse_release(self, x, y, button, modifier):
        if self.dragging:
            self.release_capture('on_mouse_drag', 'on_mouse_release')
            self.dragging = False
    
    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        if self.dragging:
            self.x += dx
            self.y += dy
            self.dispatch_event('on_move', self.x, self.y)
    
    def close(self):
        self._cancel_close = False
        self.dispatch_event('on_close')
        if not self._cancel_close:
            self.delete()
            self.dispatch_event('on_destroy')
    
    def cancel_close(self):
        self._cancel_close = True
        
Dialog.register_event_type('on_move')
Dialog.register_event_type('on_close')
Dialog.register_event_type('on_destroy')
        
        
    
if __name__ == '__main__':
    import base
    base.init_gui()
    b = Button(caption=u"进入幻想乡", x=300, y=300, width=120, height=60)
    Button(x=400, y=400, width=200, height=60)
    Button(x=450, y=450, width=200, height=60)
    Dialog(caption="hahaha", x=100, y=100, width=300, height=300)
    Dialog(caption="hahaha", x=100, y=100, width=300, height=300)
    dd = Dialog(caption="hahaha", x=100, y=100, width=300, height=300)
    Dialog(caption="hohoho", x=10, y=10, width=100, height=100, parent=dd)
    Button(caption=u"进入幻想乡1", x=230, y=30, width=120, height=60, parent=dd)
    
    @b.event
    def on_click():
        print 'Clicked!'
    
    @dd.event
    def on_close():
        dd.cancel_close()
        
    pyglet.app.run()
