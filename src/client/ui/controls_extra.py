# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from client.ui.base.interp import SineInterp, InterpDesc
from utils import Rect

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
    x = InterpDesc('_x')
    y = InterpDesc('_y')
    shine_alpha = InterpDesc('_shine_alpha')
    def __init__(self, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 91, 125
        self.img = pyglet.image.load('/home/proton/Desktop/res/wzsy.tga')
        self.img_shine = pyglet.image.load('/home/proton/Desktop/res/shine_soft.tga')
        self.shine = False
        self.gray = False
        self.x, self.y,  = x, y
        self.shine_alpha = 0.0

    def draw(self, dt):
        if self.gray:
            glColor4f(.66, .66, .66, 1.)
        else:
            glColor4f(1., 1., 1., 1.)
        self.img.blit(0, 0)
        glColor4f(1., 1., 1., self.shine_alpha)
        self.img_shine.blit(-6, -6)

    def on_mouse_enter(self, x, y):
        self.shine_alpha = 1.0

    def on_mouse_leave(self, x, y):
        self.shine_alpha = SineInterp(1.0, 0.0, 0.3)

    def animate_to(self, x, y):
        self.x = SineInterp(self.x, x, 0.3)
        self.y = SineInterp(self.y, y, 0.3)

class CardArea(Control):

    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 93*5, 125
        self.cards = []

    def draw(self, dt):
        self.draw_subcontrols(dt)

    def _update(self):
        n = len(self.cards)
        width = min(5, n) * 93.0
        step = (width - 91)/(n-1) if n > 1 else 0
        for i, c in enumerate(self.cards):
            c.animate_to(2 + int(step * i), 0)

    def add_cards(self, clist):
        self.cards.extend(clist)
        for c in clist:
            c.migrate_to(self)
        self._update()

    def get_cards(self, indices, control=None):
        indices = sorted(indices, reverse=True)
        cl = [self.cards[i] for i in indices]
        for i in indices:
            c = self.cards[i]
            if control:
                c.migrate_to(control)
            else:
                c.delete()
            del self.cards[i]
        self._update()
