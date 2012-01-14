# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from base import Control

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
        anim_time = 0.5
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
    
    def draw(self, dt):
        w, h = self.width, self.height
        glPushAttrib(GL_POLYGON_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glColor3f(1.0, 1.0, 1.0)
        glRecti(0, 0, w, h)
        glColor3f(0, 0, 0)
        self.label.draw()
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, w, h)
        graphics.draw(5, GL_LINE_STRIP,('v2i', (
            0, h-16,
            w, h-16,
            w-16, h,
            w-16, h-16,
            w, h,
        )))
        glPopAttrib()
    
    #TODO: event: on_move, dialog_close
        
        
    
if __name__ == '__main__':
    import base
    base.init_gui()
    #b = Button(caption=u"进入幻想乡", x=300, y=300, width=120, height=60)
    #Button(x=400, y=400, width=200, height=60)
    #Button(x=450, y=450, width=200, height=60)
    Dialog(caption="hahaha", x=100, y=100, width=300, height=300)
    #@b.event
    #def on_click():
    #    print 'Clicked!'
        
    pyglet.app.run()