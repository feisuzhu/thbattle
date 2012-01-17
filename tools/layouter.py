# -*- coding: utf-8 -*-
import sys
from pyglet.window import key
from pyglet.text import Label as RawLabel

sys.path.append('../src')

import pyglet
from pyglet.gl import *

from client.ui.base import Control, WINDOW_WIDTH, WINDOW_HEIGHT, init_gui, Button, TextBox, Dialog

class Layouter(Control):
    def __init__(self, *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)
        self.set_focus()
        self.index = 0
        class Dummy(object):
            def _do_draw(self, dt): pass
            x = 0
            y = 0
            width = 0
            height = 0
        self.add_control(Dummy())
        self.flash = False
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.x = 0
        self.y = 0
        self.scale = 1
        self.set_capture('on_mouse_drag')
        def flashing(dt):
            global layout
            layout.flash = not layout.flash
        pyglet.clock.schedule_interval(flashing, 0.5)

    def on_key_press(self, symbol, modifier):
        if symbol == key.TAB:
            if modifier == key.MOD_SHIFT:
                self.index += 1
            else:
                self.index -= 1
            l = len(self.control_list)
            self.index = (self.index + l*100) % l
        elif symbol == key.SPACE:
            self.scale = 1 if self.scale != 1 else 10

    def on_text_motion(self, motion):
        dir = {
            key.MOTION_UP: (0, 1),
            key.MOTION_DOWN: (0, -1),
            key.MOTION_LEFT: (-1, 0),
            key.MOTION_RIGHT: (1, 0),
        }
        c = self.control_list[self.index]
        dd = dir.get(motion)
        c.x = c.x + dd[0] * self.scale
        c.y = c.y + dd[1] * self.scale

    def draw(self, dt):
        l = len(self.control_list)
        index = (self.index + l*100) % len(self.control_list)
        for i, c in enumerate(self.control_list):
            glPushMatrix()
            glTranslatef(c.x, c.y, 0)
            if i == index and self.flash:
                glColor3f(0.3, 0.3, 0.3)
                glRecti(0, 0, c.width, c.height)
            else:
                c._do_draw(dt)
            glPopMatrix()

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        if modifier == key.MOD_SHIFT:
            c = self.control_list[self.index]
            c.x += dx
            c.y += dy

    def on_mouse_press(self, x, y, button, modifier):
        if modifier == key.MOD_SHIFT:
            try:
                c = self.control_frompoint1(x, y)
                self.index = self.control_list.index(c)
            except:
                self.index = 0

class Label(Control):
    def __init__(self, text=u'Label',
                    font_size=30,color=(0,0,0,255),
                    x=0, y=0,
                    anchor_x='center', anchor_y='center', *a, **k):
        self.rawlabel = RawLabel(text=text, font_size=font_size,
                                 color=color,x=0,y=0,
                                 anchor_x='left', anchor_y='bottom')
        w, h = self.rawlabel.content_width, self.rawlabel.content_height
        Control.__init__(self, x=x, y=y, width=w, height=h, *a, **k)

    def draw(self, dt):
        self.rawlabel.draw()

class Rectangle(Control):
    def draw(self, dt):
        glPushAttrib(GL_POLYGON_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor3f(0,0,0)
        glRecti(0,0,self.width,self.height)
        glPopAttrib()

init_gui()
layout = Layouter()

#----------------


b = Button(caption=u"进入幻想乡", x=0, y=0, width=120, height=60, parent=layout)
Label(parent=layout)
Rectangle(widht=100, height=100, parent=layout)
b1 = Button(caption=u"进入幻想乡", x=100, y=0, width=120, height=60, parent=layout)

bbb = Button(x=400, y=400, width=200, height=60, parent=layout)
bb = Button(x=450, y=450, width=200, height=60, parent=layout)
@bb.event
def on_click():
    bbb.state = Button.DISABLED if bbb.state != Button.DISABLED else Button.NORMAL

dd = Dialog(caption="hahaha", x=100, y=100, width=300, height=150, parent=layout)
Dialog(caption="hohoho", x=10, y=10, width=100, height=100, parent=dd)
Button(caption=u"进入幻想乡1", x=230, y=30, width=120, height=60, parent=dd)

TextBox(x=50, y=50, width=300, parent=layout)
tt = TextBox(x=450, y=50, width=300, parent=layout)
#------------------
pyglet.app.run()

for i, c in enumerate(layout.control_list[1:]):
    print "#%d(%s) ==> x: %d, y:%d" % (i, c.__class__.__name__, c.x, c.y)
