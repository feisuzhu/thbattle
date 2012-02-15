# -*- coding: utf-8 -*-
import sys
from pyglet.window import key
from pyglet.text import Label as RawLabel

sys.path.append('../src')

import pyglet
from pyglet.gl import *

from client.ui.base import *
from client.ui.controls import *

class Layouter(Control):
    def __init__(self, *args, **kwargs):
        Control.__init__(self, can_focus=False, *args, **kwargs)
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
        self.set_capture('on_key_press')
        self.set_capture('on_text_motion')

        def flashing(dt):
            self.flash = not self.flash
        pyglet.clock.schedule_interval(flashing, 0.4)

    def on_key_press(self, symbol, modifier):
        _ = lambda b: modifier & b == b
        if symbol == key.TAB:
            if _(key.MOD_SHIFT):
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
        if dd:
            c.x = c.x + dd[0] * self.scale
            c.y = c.y + dd[1] * self.scale

    def draw_hook_before(self, dt):
        pass

    def draw_hook_after(self, dt):
        pass

    def draw(self, dt):
        self.draw_hook_before(dt)
        l = len(self.control_list)
        index = (self.index + l*100) % len(self.control_list)
        for i, c in enumerate(self.control_list):
            glPushMatrix()
            glTranslatef(c.x, c.y, 0)
            '''
            if i == index and self.flash:
                glColor3f(0.3, 0.3, 0.3)
                glRecti(0, 0, c.width, c.height)
            else:
                c._do_draw(dt)
            '''
            c._do_draw(dt)
            if i == index and self.flash:
                glEnable(GL_COLOR_LOGIC_OP)
                glLogicOp(GL_INVERT)
                glRecti(0, 0, c.width, c.height)
                glDisable(GL_COLOR_LOGIC_OP)

            glPopMatrix()
        self.draw_hook_after(dt)

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        _ = lambda b: modifier & b == b
        if _(key.MOD_SHIFT | key.MOD_CTRL):
            c = self.control_list[self.index]
            c.width += dx
            c.height -= dy
            c.y += dy
        elif _(key.MOD_SHIFT):
            c = self.control_list[self.index]
            c.x += dx
            c.y += dy


    def on_mouse_press(self, x, y, button, modifier):
        _ = lambda b: modifier & b == b
        if _(key.MOD_SHIFT):
            try:
                c = self.control_frompoint1(x, y)
                self.index = self.control_list.index(c)
            except:
                self.index = 0

class Label(Control):
    def __init__(self, text=u'Label',
                font_size=30, color=(0,0,0,255),
                x=0, y=0, bold=False, italic=False, *a, **k):
        self.rawlabel = RawLabel(
            text=text, font_size=font_size,
            color=color,x=0,y=0,
            anchor_x='left', anchor_y='bottom',
            bold=bold, italic=italic
        )
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
layout = Layouter(parent=Overlay.cur_overlay)
_base = None
#----------------

img = pyglet.image.load('/home/proton/Desktop/capture/snap00031.png')

from game import autoenv
autoenv.init('Client')
from client.ui import resource as cres
from gamepack.simple.ui import resource as sres
print dir(sres)
sp = pyglet.sprite.Sprite(cres.actor_frame, x=100, y=100)
interp = LinearInterp(0.0, 1.0, 1.0)

from client.ui import ui_utils

def bg(dt):
    glColor4f(1,1,1,1)
    img.blit(0,0)

layout.draw_hook_before = bg

glClearColor(0,0,0, 1.0)
#Control(parent=layout, x=35, y=20, width=700, height=180)._text = 'Chat'
#Control(parent=layout, x=35, y=220, width=700, height=420)._text = 'GameList'
#Control(parent=layout, x=750, y=220, width=240, height=420)._text = 'ControlPanel'
#Control(parent=layout, x=750, y=20, width=240, height=180)._text = 'UserInfo'

#Rectangle(parent=layout, x=545, y=166, width=78, height=24)
'''
ConfirmButtons(parent=layout, x=544, y=166, width=165, height=24)
Label(parent=layout, text=u'请选择…', x=373, y=190, font_size=12, color=(255,255,180,255), bold=True)
_base = BigProgressBar(parent=layout, x=285, y=162, width=250, height=29)
_base.value = 1.0
'''
rect = Control(parent=layout, x=285, y=162, width=531, height=58)
ConfirmButtons(parent=rect, x=259, y=4, width=165, height=24)
Label(parent=rect, text=u'请选择…', x=88, y=28, font_size=12, color=(255,255,180,255), bold=True)
BigProgressBar(parent=rect, x=0, y=0, width=250, height=29).value = 1.0

#------------------
pyglet.app.run()
if _base:
    ox, oy = _base.x, _base.y
    print 'Base: x=%d, y=%d' % (ox, oy)
else:   ox, oy = 0, 0

for i, c in enumerate(layout.control_list[1:]):
    print ("#%d(%s) ==> x=%d, y=%d, width=%d, height=%d" %
        (i, c.__class__.__name__, c.x - ox, c.y - oy, c.width, c.height))
