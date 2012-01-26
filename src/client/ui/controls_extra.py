# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from client.ui.base.interp import *
from client.ui import resource as common_res
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
    def __init__(self, name='Proton', *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 149, 195
        self.name = pyglet.text.Label(
            text=name, font_size=9,
            x=9, y=175, anchor_x='left', anchor_y='bottom'
        )
        self.selected = False

    def draw(self, dt):
        glColor3f(1, 1, 1)
        common_res.char_portrait.blit(0, 0)
        if self.selected:
            glColor4f(1, 1, 1, .3)
            glRecti(0, 0, self.width, self.height)
        self.name.draw()

class TextArea(Control):
    def __init__(self, font=None, text='Yoooooo~', *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)
        self.document = pyglet.text.document.FormattedDocument(text)
        self.document.set_style(0, len(self.document.text),
            dict(color=(0, 0, 0, 255))
        )

        width, height = self.width, self.height

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width-2, height-2, multiline=True)
        self.caret = pyglet.text.caret.Caret(self.layout)

        self.set_handlers(self.caret)
        self.push_handlers(self)

        self.layout.x = 1
        self.layout.y = 1

        from client.ui.base.baseclasses import main_window
        self.window = main_window
        self.text_cursor = self.window.get_system_mouse_cursor('text')
        self.focused = False

    def _gettext(self):
        return self.document.text

    def _settext(self, text):
        self.document.text = text

    text = property(_gettext, _settext)

    def draw(self, dt):
        glPushAttrib(GL_POLYGON_BIT)
        glColor3f(1.0, 1.0, 1.0)
        glRecti(0, 0, self.width, self.height)
        glColor3f(0.0, 0.0, 0.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, self.width, self.height)
        glPopAttrib()
        self.layout.draw()

    def on_focus(self):
        self.caret.visible = True
        self.caret.mark = 0
        self.caret.position = len(self.document.text)
        self.focused = True

    def on_lostfocus(self):
        self.caret.visible = False
        self.caret.mark = self.caret.position = 0
        self.focused = False

    def on_mouse_enter(self, x, y):
        self.window.set_mouse_cursor(self.text_cursor)

    def on_mouse_leave(self, x, y):
        self.window.set_mouse_cursor(None)

    def on_mouse_drag(self, x, y, dx, dy, btn, modifier):
        # If I'm not focused, don't select texts
        if not self.focused:
            return pyglet.event.EVENT_HANDLED

class CardSprite(Control):
    x = InterpDesc('_x')
    y = InterpDesc('_y')
    shine_alpha = InterpDesc('_shine_alpha')
    alpha = InterpDesc('_alpha')
    img_shinesoft = common_res.card_shinesoft
    width, height = 91, 125
    def __init__(self, x=0.0, y=0.0, img=None, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 91, 125
        self.shine = False
        self.gray = False
        self.x, self.y,  = x, y
        self.shine_alpha = 0.0
        self.alpha = 1.0
        self.img = img

    def draw(self, dt):
        if self.gray:
            glColor4f(.66, .66, .66, self.alpha)
        else:
            glColor4f(1., 1., 1., self.alpha)
        self.img.blit(0, 0)
        glColor4f(1., 1., 1., self.shine_alpha)
        self.img_shinesoft.blit(-6, -6)

    def on_mouse_enter(self, x, y):
        self.shine_alpha = 1.0

    def on_mouse_leave(self, x, y):
        self.shine_alpha = SineInterp(1.0, 0.0, 0.3)

class HandCardArea(Control):
    width, height = 93*5+42, 145
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 93*5+42, 145
        self.cards = []
        self.selected = []

    def draw(self, dt):
        glColor4f(1,1,1,1)
        self.draw_subcontrols(dt)

    def _update(self):
        n = len(self.cards)
        width = min(5*93.0+42, n*93.0)
        step = (width - 91)/(n-1) if n > 1 else 0
        for i, c in enumerate(self.cards):
            c.zindex = i
            sel = self.selected[i]
            c.x = SineInterp(c.x, 2 + int(step * i), 0.3)
            c.y = SineInterp(c.y, 20 if sel else 0, 0.3)

    def add_cards(self, clist):
        self.cards.extend(clist)
        self.selected.extend([False] * len(clist))
        self._update()

    def get_cards(self, indices, control=None):
        indices = sorted(indices, reverse=True)
        cl = [self.cards[i] for i in indices]
        for i in indices:
            del self.cards[i]
        self.selected = [False] * len(self.cards)
        self._update()
        return cl

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        if c:
            try:
                i = self.cards.index(c)
            except:
                return
            self.selected[i] = not self.selected[i]
            c.y = SineInterp(c.y, 20 if self.selected[i] else 0, 0.1)

class DropCardArea(Control):
    width, height = 820, 125
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 820, 125
        self.cards = []
        self.need_update = True

    def draw(self, dt):
        if self.need_update:
            self.need_update = False
            for c in self.control_list[:]:
                tbl = dict(zip(self.cards, [True]*len(self.cards)))
                if not tbl.get(c):
                    c.delete()
            self._update()
        glColor4f(1,1,1,1)
        self.draw_subcontrols(dt)

    def _update(self):
        n = len(self.cards)
        x = (820-n*93)/2
        step = 93
        for i, c in enumerate(self.cards):
            c.zindex = i
            c.x = SineInterp(c.x, x + int(step * i), 0.3)
            c.y = SineInterp(c.y, 0, 0.3)

    def _on_cardanimdone(self, card, desc):
        # Can't remove it here, or
        # the card next will not be drawn,
        # causes a flash
        # card.delete()
        self.cards.remove(card)
        self.need_update = True

    def add_cards(self, clist):
        self.cards.extend(clist)
        for c in clist:
            c.alpha = ChainInterp(
                FixedInterp(1.0, 3),
                CosineInterp(1.0, 0.0, 1),
                on_done=self._on_cardanimdone,
            )
        self._update()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

class Ray(Control):
    img_ray = common_res.ray
    scale = InterpDesc('_scale')
    alpha = InterpDesc('_alpha')

    def __init__(self, f, t, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        # f, t should be [GameCharacterPortrait]s
        from math import sqrt
        self.x, self.y = f.x + f.width/2, f.y + f.height/2
        dx, dy = t.x-f.x, t.y-f.y
        scale = sqrt(dx*dx+dy*dy) / self.img_ray.width
        self.angle = atan(1.0 * dy / dx)
        self.scale = SineInterp(1.0, scale, 0.3)
        self.alpha = ChainInterp(
            FixedInterp(1.0, 0.3),
            CosineInterp(1.0, 0.0, 0.2),
        )

    def draw(self, dt):
        glPushMatrix()
        glRotatef(self.angle, 0., 0., 1.)
        glScalef(self.scale, 1., 1.)
        self.img_ray.blit(0,0)
        glPopMatrix()

        if self._alpha.finished: # the ChainInterp
            self.delete()
