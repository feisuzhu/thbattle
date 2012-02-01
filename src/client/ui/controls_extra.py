# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from client.ui.base.interp import *
from client.ui import resource as common_res
from utils import Rect, ScissorBox, InvalidScissorBox

import logging
log = logging.getLogger('UI_ControlsExtra')


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
        self.maxlife = 8
        self.life = 0

    def draw(self, dt):
        glColor3f(1, 1, 1)
        common_res.char_portrait.blit(0, 0)
        if self.selected:
            glColor4f(1, 1, 1, .3)
            glRecti(0, 0, self.width, self.height)
        self.name.draw()

        hp, hp_bg = common_res.hp, common_res.hp_bg

        tw, th = self.maxlife, 1
        vw, vh = hp_bg.width * self.maxlife, hp_bg.height

        glPushMatrix()
        glTranslatef(5., 55., 0)

        glEnable(hp_bg.target)
        glBindTexture(hp_bg.target, hp_bg.id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(tw, 0); glVertex2f(vw, 0)
        glTexCoord2f(tw, th); glVertex2f(vw, vh)
        glTexCoord2f(0, th); glVertex2f(0, vh)
        glEnd()
        #glDisable(hp_bg.target) # both GL_TEXTURE_2D, save the calls

        tw, th = self.life, 1
        vw, vh = hp.width * self.life, hp.height
        #glEnable(hp.target)
        glBindTexture(hp.target, hp.id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(tw, 0); glVertex2f(vw, 0)
        glTexCoord2f(tw, th); glVertex2f(vw, vh)
        glTexCoord2f(0, th); glVertex2f(0, vh)
        glEnd()
        glDisable(hp.target)
        glPopMatrix()

class TextArea(Control):
    def __init__(self, font='Arial', font_size=9, *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)

        width, height = self.width, self.height

        self.document = doc = pyglet.text.document.FormattedDocument(u'\u200b')
        self.default_attrib = dict(
            font_size=font_size, font_name=font,
            bold=False, italic=False,
            underline=None, color=(0, 0, 0, 255),
        )

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width-2, height-2, multiline=True)

        self.layout.x = 1
        self.layout.y = 1

        self._text = ''
        self.append(text)

    def _gettext(self):
        return self._text

    def _settext(self, text):
        self._text = ''
        self.document.text = u'\u200b'
        self.append(text)

    def append(self, text):
        attrib = dict(self.default_attrib)
        doc = self.document

        def set_attrib(entry, val):
            def scanner_cb(s, tok):
                attrib[entry] = val
            return scanner_cb

        def restore(s, tok):
            attrib = dict(self.default_attrib)

        def instext(s, tok):
            # *MEGA* HACK:
            # pyglet's layout won't snap long words,
            # and this is unacceptable for chinese characters!!!!
            # so inserting ZeroWidthSpace[ZWSP] here.
            tok = unicode(tok)
            tok = u'\u200b'.join(tok) + u'\u200b'
            doc.insert_text(len(doc.text), tok, attrib)

        def color(s, tok):
            c = tok[2:]
            color = (
                int(c[0:2], 16),
                int(c[2:4], 16),
                int(c[4:6], 16),
                int(c[6:8], 16),
            )
            attrib['color'] = color

        def insert_pipe(s, tok):
            instext(s, '|')

        import re
        scanner = re.Scanner([
            (r'[^|]+', instext),
            (r'\|c[A-Fa-f0-9]{8}', color),
            (r'\|B', set_attrib('bold', True)),
            (r'\|b', set_attrib('bold', False)),
            (r'\|I', set_attrib('italic', True)),
            (r'\|i', set_attrib('italic', False)),
            (r'\|U', set_attrib('underline', (0,0,0,255))),
            (r'\|u', set_attrib('underline', None)),
            (r'\|\|', insert_pipe),
            (r'\|r', restore),
        ])

        self.layout.begin_update()
        toks, reminder = scanner.scan(text)
        if reminder:
            log.error('text scanning failed: %s', text)
        # *MEGA* HACK:
        # make the ZeroWidthSpace(ZWSP) char invisible
        for start, end, font in doc.get_font_runs().ranges(0, 999999):
            zwsp = font.get_glyphs(u'\u200b')[0]
            zwsp.vertices = (0, 0, 0, 0)
            zwsp.advance = 0
        self.layout.end_update()
        self.layout.view_y = -self.layout.content_height
        self._text += text

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

    def on_mouse_scroll(self, x, y, dx, dy):
        f = self.document.get_font(0)
        size = f.ascent - f.descent
        self.layout.view_y += dy * size*2

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
        from math import sqrt, atan2, pi
        self.x, self.y = f.x + f.width/2, f.y + f.height/2
        dx, dy = t.x-f.x, t.y-f.y
        scale = sqrt(dx*dx+dy*dy) / self.img_ray.width
        self.angle = atan2(dy, dx) / pi * 180
        self.scale = SineInterp(0.0, scale, 0.4)
        self.alpha = ChainInterp(
            FixedInterp(1.0, 1),
            CosineInterp(1.0, 0.0, 0.5),
            on_done=lambda self, desc: self.delete()
        )

    def draw(self, dt):
        glPushMatrix()
        glRotatef(self.angle, 0., 0., 1.)
        glScalef(self.scale, 1., 1.)
        glTranslatef(0., -self.img_ray.height/2, 0.)
        glColor4f(1., 1., 1., self.alpha)
        self.img_ray.blit(0,0)
        glPopMatrix()

    def hit_test(self, x, y):
        return False

class ListItem(object):
    def __init__(self, p):
        self.parent = p
        n = len(p.columns)
        self.labels = [None] * n
        self._data = [''] * n
        self.data = ['Yoo~'] * n
        self.line_height = p.font_height + 1
        self.selected = False

    def _set_data(self, val):
        val = list(val)
        p = self.parent
        n = len(p.columns)
        val = (val + n*[''])[:n]
        for i, v in enumerate(val):
            self[i] = v

    def _get_data(self):
        return self._data

    data = property(_get_data, _set_data)

    def __getitem__(self, index):
        if isinstance(index, basestring):
            index = self.parent.col_lookup[index]
        return self._data[index]

    def __setitem__(self, index, val):
        from pyglet.text import Label
        p = self.parent
        if isinstance(index, basestring):
            index = p.col_lookup[index]
        self._data[index] = val
        self.labels[index] = Label(
            text=str(val), font_name=p.font, font_size=p.font_size,
            anchor_x='left', anchor_y = 'bottom', color=(0,0,0,255),
        )

    def draw(self, bx, by):
        lh = self.line_height
        p = self.parent
        w = p.width
        glColor3f(1,1,1)
        glRecti(bx, by, bx+w, by+lh)
        glColor3f(0,0,0)
        glBegin(GL_LINES)
        glVertex2f(bx, by); glVertex2f(bx+w, by)
        glVertex2f(bx, by+lh); glVertex2f(bx+w, by+lh)
        ox = 0
        for _, w in p.columns + [('', 0)]:
            glVertex2f(bx+ox, by)
            glVertex2f(bx+ox, by+lh)
            ox += w
        glEnd()
        ox = 0
        for (_, w), lbl in zip(p.columns, self.labels):
            lbl.x, lbl.y = bx + ox, by
            lbl.draw()
            ox += w

        if self.selected:
            glColor4f(0, 0, 1, 0.3)
            glRecti(bx, by, bx+p.width, by+lh)

class ListView(Control):
    li_class = ListItem
    lh_class = ListItem
    header_height = 20
    def __init__(self, font_name='Arial', font_size=10, *a, **k):
        Control.__init__(self, *a, **k)
        self.font, self.font_size = font_name, font_size
        f = pyglet.font.load(font_name, font_size)
        self.font_height = f.ascent - f.descent
        self.items = []
        self.columns = []
        self.col_lookup = {}
        self._view_y = self.header_height

    def set_columns(self, cols):
        # [('name1', 20), ('name2', 30)]
        self.columns = list(cols)
        self.col_lookup = {
            name: index
            for index, (name, width) in enumerate(cols)
        }
        self.header = self.lh_class(self)
        self.header.line_height = self.header_height
        self.header.data = [n for n, w in cols]

    def append(self, val):
        if isinstance(val, ListItem):
            li = val
            li.parent = self
        elif isinstance(val, (list, tuple)):
            li = self.li_class(self)
            li.data = val
        self.items.append(li)
        return li

    def clear(self):
        self.items = []

    def _set_view_y(self, val):
        sum_h = sum(li.line_height for li in self.items)
        lhh = self.header.line_height
        if val > lhh: val = lhh
        bot_lim = -sum_h + self.height - 10
        if val < bot_lim: val = bot_lim
        self._view_y = val

    def _get_view_y(self):
        return self._view_y

    view_y = property(_get_view_y, _set_view_y)

    def draw(self, dt):
        w, h = self.width, self.height - self.header.line_height
        self.header.draw(0, h)
        try:
            # GUIDO Y U REJECT PEP377 !!
            with ScissorBox(self, -1, -1, w+2, h+2):
                # for a consistent design with pyglet.text.layout
                # view_y uses negative values
                y = self.height - self.view_y
                for li in self.items:
                    lh = li.line_height
                    y -= lh
                    if y > h: continue
                    if y < -lh: break
                    li.draw(0, y)
        except InvalidScissorBox:
            pass

    def on_mouse_scroll(self, x, y, dx, dy):
        self.view_y += dy * 40

    def on_mouse_click(self, x, y, button, modifier):
        ly = self.height - self.view_y
        for li in self.items:
            li.selected = False
            lh = li.line_height
            if ly > y > ly - lh:
                li.selected = True
            ly -= lh
