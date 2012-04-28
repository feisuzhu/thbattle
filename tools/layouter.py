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
            def draw(self): pass
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

    def draw_hook_before(self):
        pass

    def draw_hook_after(self):
        pass

    def draw(self):
        self.draw_hook_before()
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
            c.draw()
            if i == index and self.flash:
                glEnable(GL_COLOR_LOGIC_OP)
                glLogicOp(GL_INVERT)
                glRecti(0, 0, c.width, c.height)
                glDisable(GL_COLOR_LOGIC_OP)

            glPopMatrix()
        self.draw_hook_after()

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

    def draw(self):
        self.rawlabel.draw()

class Rectangle(Control):
    def draw(self):
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
#img = pyglet.image.load('/dev/shm/1.png')
from game import autoenv
autoenv.init('Client')
from client.ui import resource as cres
from gamepack.thb.ui.game_controls import *
from gamepack.thb.ui import resource as gres
from utils import BatchList

def bg():
    glColor4f(1,1,1,1)
    img.blit(0,0)

layout.draw_hook_before = bg

from gamepack.thb.cards import *

c = AttackCard(1, 1)

cs = CardSprite(c, parent=layout)

cs.init_ballon_text('|Ghahahah!|r\n\nasdfasdfasdfasdfasdfa\nsdfasdfasdfasdf')


#------------------
pyglet.app.run()
if _base:
    ox, oy = _base.x, _base.y
    print 'Base: x=%d, y=%d' % (ox, oy)
else:   ox, oy = 0, 0

for i, c in enumerate(layout.control_list[1:]):
    print ("#%d(%s) ==> x=%d, y=%d, width=%d, height=%d" %
        (i, c.__class__.__name__, c.x - ox, c.y - oy, c.width, c.height))
