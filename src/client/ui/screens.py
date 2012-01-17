# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from client.ui.base import Overlay
from pyglet.text import Label

class LoadingScreen(Overlay):

    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)

        self.label = Label(text='Loading',
                    font_size=60,color=(255,255,255,255),
                    x=self.width//2, y=self.height//2,
                    anchor_x='center', anchor_y='center')

    def draw(self, dt):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.label.draw()

class LoginScreen(Overlay):

    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.batch = pyglet.graphics.Batch()
        self.title = Label(text='GENSOUKILL',
                    font_size=60,color=(0,0,0,255),
                    x=self.width*.618, y=self.height//2,
                    anchor_x='center', anchor_y='center',
                    batch=self.batch)
        x, y, w, h = 350, 165, 325, 160
        x1, y1 = x + w, y + h
        self.batch.add(5, GL_LINES_STRIP, None,
                       ('v2i', [
                        x, y, x1, y,
                        x1, y1, x, y1,
                        x, y]),
                       ('c3f', [0.0, 0.0, 0.0] * 5))
        self.lbl_uname = Label(text=u'用户名',
                    font_size=12,color=(0,0,0,255),
                    x=self.width*.618, y=self.height//2,
                    anchor_x='center', anchor_y='center',
                    batch=self.batch)
        self.lbl_pwd = Label(text=u'密码',
                    font_size=12,color=(0,0,0,255),
                    x=self.width*.618, y=self.height//2,
                    anchor_x='center', anchor_y='center',
                    batch=self.batch)

    def draw(self, dt):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.batch.draw()
        self.draw_subcontrols()
