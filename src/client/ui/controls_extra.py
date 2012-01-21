# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from utils.geometry import Rect

class PlayerPortrait(Control):
    def __init__(self, player_name, color=[0,0,0], *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.width, self.height = 128, 245
        self.player_name = player_name
        self.color = color
        self.refresh()

    def refresh(self):
        from pyglet.text import Label
        self.batch = pyglet.graphics.Batch()
        self.label = Label(
            text=self.player_name, font_size=9, bold=True, color=(0,0,0,255),
            x=128//2, y=245//2, anchor_x='center', anchor_y='center',
            batch=self.batch
        )
        r = Rect(0, 0, 128, 245)
        self.batch.add(
            5, GL_LINE_STRIP, None,
            ('v2i', r.glLineStripVertices()),
            ('c3i', self.color * 5)
        )

    def draw(self, dt):
        self.batch.draw()

class GameCharacterPortrait(Control):
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 149, 195

class TextArea(Control):
    def __init__(self, color=(0,0,0), *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        from pyglet.text import Label
        self.batch = pyglet.graphics.Batch()
        self.label = Label(
            text='TextArea', font_size=12, color=(0,0,0,255),
            x=self.width//2, y=self.height//2,
            anchor_x='center', anchor_y='center', batch=self.batch
        )
        r = Rect(0, 0, self.width, self.height)
        self.batch.add(
            5, GL_LINE_STRIP, None,
            ('v2i', r.glLineStripVertices()),
            ('c3i', color * 5),
        )

    def draw(self, dt):
        self.batch.draw()

class CardSprite(Control):
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 91, 125
        self.img = pyglet.image.load('/home/proton/Desktop/res/wzsy.tga')

    def draw(self, dt):
        self.img.blit(0, 0)

class CardArea(Control):
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 93*5, 125
        self.cards = []

    def draw(self, dt):
        self.draw_subcontrols(dt)

    def update(self):
        n = len(self.cards)
        width = min(5, n) * 93.0

        step = int((width - 91)/(n-1))

        for i in xrange(n):
            self.cards[i].x = 2 + step * i
