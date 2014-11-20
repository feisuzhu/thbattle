# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from pyglet.gl import GL_CLIENT_VERTEX_ARRAY_BIT, GL_QUADS, GL_T2F_C4F_N3F_V3F, GL_T4F_V4F, GLfloat
from pyglet.gl import glColor3f, glColor4f, glDrawArrays, glInterleavedArrays, glLoadIdentity
from pyglet.gl import glPopClientAttrib, glPopMatrix, glPushClientAttrib, glPushMatrix, glRectf
from pyglet.gl import glRotatef, glScalef, glTranslatef
from pyglet.text import Label
import pyglet

# -- own --
from .. import actions
from ..cards import CardList
from client.ui.base import Control
from client.ui.base.interp import AbstractInterp, ChainInterp, CosineInterp, FixedInterp, InterpDesc
from client.ui.base.interp import LinearInterp, SineInterp, getinterp
from client.ui.controls import BalloonPrompt, Button, Colors, Frame, ImageButton, OptionButton
from client.ui.controls import Panel, TextArea
from client.ui.resloader import L, get_atlas
from game.autoenv import Game
from utils import flatten, rectv2f, rrectv2f


# -- code --
class CardSprite(Control):
    x                = InterpDesc('_x')
    y                = InterpDesc('_y')
    back_scale       = InterpDesc('_bs')
    question_scale   = InterpDesc('_qs')
    ftanim_alpha     = InterpDesc('_fta')
    ftanim_cardalpha = InterpDesc('_ftca')
    shine_alpha      = InterpDesc('_shine_alpha')
    alpha            = InterpDesc('_alpha')
    width, height    = 91, 125

    def __init__(self, card, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)

        self._w, self._h = 91, 125
        self.shine = False
        self.gray = False
        self.x, self.y = x, y
        self.shine_alpha = 0.0
        self.selected = False
        self.alpha = 1.0
        self.card = card

        self.ft_anim = False
        self.balloon = BalloonPrompt(self)

        self.update()

    @staticmethod
    def batch_draw(csl):
        glPushMatrix()
        glLoadIdentity()

        vertices = []
        for cs in csl:
            ax, ay = cs.abs_coords()
            if cs.ft_anim:
                qs = cs.question_scale
                bs = cs.back_scale
                aa = cs.ftanim_alpha
                ca = cs.ftanim_cardalpha
                if cs.gray:
                    c = (.66, .66, .66, ca)
                else:
                    c = (1., 1., 1., ca)
                vertices += cs.img.get_t2c4n3v3_vertices(c, ax, ay)

                n, s = cs.number, cs.suit
                if n: vertices += L('thb-cardnum')[s % 2 * 13 + n - 1].get_t2c4n3v3_vertices(c, ax + 5, ay + 105)
                if s: vertices += L('thb-suit')[s - 1].get_t2c4n3v3_vertices(c, ax + 6, ay + 94)

                c = (1, 1, 1, aa)

                if qs:
                    vertices += L('thb-card-question').get_t2c4n3v3_vertices(c, ax+(1-qs)*45, ay, 0, qs*91)

                if bs:
                    vertices += L('thb-card-hidden').get_t2c4n3v3_vertices(c, ax+(1-bs)*45, ay, 0, bs*91)
            else:
                a = cs.alpha
                if cs.gray:
                    c = (.66, .66, .66, a)
                else:
                    c = (1., 1., 1., a)
                vertices += cs.img.get_t2c4n3v3_vertices(c, ax, ay)
                resides_in = cs.card.resides_in
                if resides_in and resides_in.type == 'showncards':
                    vertices += L('thb-card-showncardtag').get_t2c4n3v3_vertices(c, ax, ay)

                n, s = cs.number, cs.suit
                if n: vertices += L('thb-cardnum')[s % 2 * 13 + n - 1].get_t2c4n3v3_vertices(c, ax + 5, ay + 105)
                if s: vertices += L('thb-suit')[s-1].get_t2c4n3v3_vertices(c, ax+6, ay+94)

                if cs.selected:
                    c = (0., 0., 2., 1.0)
                else:
                    c = (1., 1., 1., cs.shine_alpha)

                vertices += L('thb-card-shinesoft').get_t2c4n3v3_vertices(c, ax-6, ay-6)

        if vertices:
            n = len(vertices)
            buf = (GLfloat*n)()
            buf[:] = vertices
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glInterleavedArrays(GL_T2F_C4F_N3F_V3F, 0, buf)
            with get_atlas('card').texture:
                glDrawArrays(GL_QUADS, 0, n/12)
            glPopClientAttrib()

        glPopMatrix()

    def update(self):
        card = self.card
        meta = card.ui_meta

        self.img = L(meta.image)

        self.number, self.suit = card.number, card.suit

        t = getattr(meta, 'description', None)
        t and self.balloon.set_balloon(t)

    def on_mouse_enter(self, x, y):
        self.shine_alpha = 1.0

    def on_mouse_leave(self, x, y):
        self.shine_alpha = SineInterp(1.0, 0.0, 0.3)

    def do_fatetell_anim(self):
        self.ft_anim = True
        self.question_scale = ChainInterp(
            SineInterp(0.0, 1.0, 0.1),
            CosineInterp(1.0, 0.0, 0.1),
            FixedInterp(0.0, 0.2),
            SineInterp(0.0, 1.0, 0.1),
            CosineInterp(1.0, 0.0, 0.1),
            FixedInterp(0.0, 0.2),
            SineInterp(0.0, 1.0, 0.1)
        )
        self.back_scale = ChainInterp(
            FixedInterp(0.0, 0.2),
            SineInterp(0.0, 1.0, 0.1),
            CosineInterp(1.0, 0.0, 0.1),
            FixedInterp(0.0, 0.2),
            SineInterp(0.0, 1.0, 0.1),
            CosineInterp(1.0, 0.0, 0.1),
        )
        self.ftanim_alpha = ChainInterp(
            FixedInterp(1.0, 1.0),
            LinearInterp(1.0, 0.0, 2.0),
            on_done=self._end_ft_anim,
        )
        self.ftanim_cardalpha = ChainInterp(
            FixedInterp(0.0, 1.0),
            FixedInterp(1.0, 0.0),
        )

    def _end_ft_anim(self, _self, desc):
        self.ft_anim = False


@staticmethod
def cardarea_batch_draw(cl):
    csl = []
    for c in cl:
        csl += c.control_list
    CardSprite.batch_draw(csl)


class HandCardArea(Control):
    def __init__(self, fold_size=5, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.fold_size = fold_size
        self.view = kwargs['parent']

    batch_draw = cardarea_batch_draw

    def update(self):
        fsz = self.fold_size
        n = len(self.control_list)
        width = min(fsz * 93.0 + 42, n * 93.0)
        step = (width - 91)/(n - 1) if n > 1 else 0
        for i, c in enumerate(self.control_list):
            c.zindex = i
            try:
                sel = c.hca_selected
            except AttributeError:
                sel = c.hca_selected = False
            c.x = SineInterp(c.x, 2 + int(step * i), 0.6)
            c.y = SineInterp(c.y, 20 if sel else 0, 0.6)

    def toggle(self, c, t):
        s = c.hca_selected = not c.hca_selected
        c.y = SineInterp(c.y, 20 if s else 0, t)
        self.view.selection_change.notify()

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        c and self.toggle(c, 0.1)

    cards = property(
        lambda self: self.control_list,
        lambda self, x: setattr(self, 'control_list', x)
    )


class PortraitCardArea(Control):
    def hit_test(self, x, y):
        return False

    batch_draw = cardarea_batch_draw

    def arrange(self):
        csl = self.control_list
        if not csl: return
        n = len(csl)

        w, h, = self.width, self.height
        offs = 20
        csw = offs * (n-1) + 93
        cor_x, cor_y = (w - csw)/2, (h - 125)/2
        for i, cs in enumerate(csl):
            if isinstance(getinterp(cs, 'x'), AbstractInterp):
                cs.x = SineInterp(cs.x, i*offs + cor_x, 0.6)
                cs.y = SineInterp(cs.y, cor_y, 0.6)
            else:
                cs.x, cs.y = i*offs + cor_x, cor_y

    def update(self):
        csl = self.control_list
        if not csl: return
        n = len(csl)

        w, h, = self.width, self.height
        offs = 20
        csw = offs * (n-1) + 93
        cor_x, cor_y = (w - csw)/2, (h - 125)/2
        for i, cs in enumerate(csl):
            cs.x = SineInterp(cs.x, i*offs + cor_x, 0.6)
            cs.y = SineInterp(cs.y, cor_y, 0.6)

    def fade(self):
        for cs in self.control_list:
            cs.alpha = ChainInterp(
                FixedInterp(1.0, 0.45),
                CosineInterp(1.0, 0.0, 0.3),
                on_done=self._on_cardanimdone,
            )

    def _on_cardanimdone(self, card, desc):
        card.delete()


class DropCardArea(Control):
    def __init__(self, fold_size=5, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.fold_size = fold_size

    batch_draw = cardarea_batch_draw

    def update(self):
        fsz = self.fold_size
        n = len(self.control_list)
        width = min(fsz*93.0, n*93.0)
        step = (width - 91)/(n-1) if n > 1 else 0

        if step < 30:
            step = 30
            width = (n-1)*30 + 93

        ox = (self.width - width) // 2

        for i, c in enumerate(self.control_list):
            c.zindex = i
            c.x = SineInterp(c.x, 2 + ox + int(step * i), 0.5)
            c.y = SineInterp(c.y, 0, 0.5)

    def fade(self):
        for cs in self.control_list:
            try:
                cs.dca_tag
                continue
            except AttributeError:
                cs.dca_tag = 1

            cs.alpha = ChainInterp(
                FixedInterp(1.0, 3),
                CosineInterp(1.0, 0.0, 1),
                on_done=self._on_cardanimdone,
            )

    def _on_cardanimdone(self, card, desc):
        card.delete()
        self.update()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)


class Ray(Control):
    scale = InterpDesc('_scale')
    alpha = InterpDesc('_alpha')

    def __init__(self, x0, y0, x1, y1, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        from math import sqrt, atan2, pi
        self.x, self.y = x0, y0
        dx, dy = x1 - x0, y1 - y0
        scale = sqrt(dx*dx+dy*dy) / L('c-ray').width
        self.angle = atan2(dy, dx) / pi * 180
        self.scale = SineInterp(0.0, scale, 0.4)
        self.alpha = ChainInterp(
            FixedInterp(1.0, 1),
            CosineInterp(1.0, 0.0, 0.5),
            on_done=lambda self, desc: self.delete()
        )

    def draw(self):
        ray = L('c-ray')
        glPushMatrix()
        glRotatef(self.angle, 0., 0., 1.)
        glScalef(self.scale, 1., 1.)
        glTranslatef(0., -ray.height/2, 0.)
        glColor4f(1., 1., 1., self.alpha)
        ray.blit(0, 0)
        glPopMatrix()

    def hit_test(self, x, y):
        return False


class SkillSelectionBox(Control):
    class SkillButton(Button):
        def __init__(self, skill, sid, enable, view, *a, **k):
            Button.__init__(self, skill.ui_meta.name, width=71, height=20, *a, **k)
            self._selected = False
            self.state = Button.NORMAL if enable else Button.DISABLED
            self.color = Colors.blue
            self.skill = skill
            self.sid = sid
            self.view = view
            self.params_ui = None
            self.update()

        @property
        def selected(self):
            return self._selected

        @selected.setter
        def selected(self, value):
            value = bool(value)
            if value == self._selected: return
            if value:
                self.color = Colors.orange
                self.update()
                self.parent.selection.append(self.sid)
                self._selected = True
                pui = getattr(self.skill.ui_meta, 'params_ui', None)
                if pui:
                    self.params_ui = pui(parent=self.view)

            else:
                self.parent.selection.remove(self.sid)
                self.color = Colors.blue
                self._selected = False
                self.update()
                ui = self.params_ui
                ui and ui.delete()

        def on_click(self):
            self.selected = not self.selected
            self.view.selection_change.notify()

        def delete(self):
            self.params_ui and self.params_ui.delete()
            Button.delete(self)

    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.selection = []

    def set_skills(self, lst):
        # lst = ((skill1, sid1, enable), (skill2, sid2, enable), ...)
        y = self.height
        for b in self.buttons[:]:
            b.delete()

        assert not self.buttons

        for skill, sid, enable in lst:
            y -= 22
            SkillSelectionBox.SkillButton(skill, sid, enable, self.parent, parent=self, x=0, y=y)

        self.selection = []

    @property
    def buttons(self):
        return self.control_list

    def get_selected_index(self):
        return self.selection

    def reset(self):
        for c in self.buttons:
            c.selected = False

        self.parent.selection_change.notify()

    def draw(self):
        self.draw_subcontrols()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)


class SmallCardSprite(Control):
    width, height = 33, 46
    x = InterpDesc('_x')
    y = InterpDesc('_y')

    def __init__(self, card, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 33, 46
        self.x, self.y = x, y
        self.selected = False
        self.hover = False
        self.card = card

        self.img = L(card.ui_meta.image_small)
        self.balloon = balloon = BalloonPrompt(self)
        balloon.set_balloon(card.ui_meta.description)

    @staticmethod
    def batch_draw(csl):
        glPushMatrix()
        glLoadIdentity()
        vertices = []
        for cs in csl:
            ax, ay = cs.abs_coords()
            vertices += cs.img.get_t4f_v4f_vertices(ax, ay)

            s = cs.card.suit
            n = cs.card.number

            ssuit = L('thb-smallsuit')
            snum = L('thb-smallnum')

            if n == 10:  # special case
                # g[0].blit(1+g[0].vertices[0], 33+g[0].vertices[1])
                # g[1].blit(5+g[1].vertices[0], 33+g[1].vertices[1])
                vertices += snum[s % 2 * 14 + 10].get_t4f_v4f_vertices(ax - 1, ay + 31)
                vertices += snum[s % 2 * 14 + 0].get_t4f_v4f_vertices(ax + 3, ay + 31)
            else:
                vertices += snum[s % 2 * 14 + n].get_t4f_v4f_vertices(ax + 1, ay + 31)

            vertices += ssuit[s - 1].get_t4f_v4f_vertices(ax + 1, ay + 22)

            if cs.selected:
                vertices += L('thb-card-small-selected').get_t4f_v4f_vertices(ax, ay)
            else:
                vertices += L('thb-card-small-frame').get_t4f_v4f_vertices(ax, ay)

        n = len(vertices)
        buf = (GLfloat*n)()
        buf[:] = vertices
        glColor3f(1., 1., 1.)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glInterleavedArrays(GL_T4F_V4F, 0, buf)
        with get_atlas('card').texture:
            glDrawArrays(GL_QUADS, 0, n/8)

        glPopClientAttrib()
        glPopMatrix()


class EquipCardArea(Control):
    def __init__(self, fold_size=4, view=None, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.width, self.height = 35*4, 46
        self.fold_size = fold_size
        self.selectable = False
        self.view = view

    @staticmethod
    def batch_draw(cl):
        csl = []
        for c in cl:
            csl += c.control_list
        SmallCardSprite.batch_draw(csl)

    def update(self):
        fsz = self.fold_size
        n = len(self.control_list)
        width = min(fsz*35.0, n*35.0)
        step = int((width - 34) / (n - 1)) if n > 1 else 0
        for i, c in enumerate(self.control_list):
            c.zindex = i
            c.x = SineInterp(c.x, 2 + step * i, 0.4)
            c.y = SineInterp(c.y, 0, 0.4)

    def on_mouse_click(self, x, y, button, modifier):
        if not self.selectable: return
        c = self.control_frompoint1(x, y)
        if c:
            c.selected = not c.selected
            self.view and self.view.selection_change.notify()

    def clear_selection(self):
        for c in self.control_list:
            c.selected = False

        self.view and self.view.selection_change.notify()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    cards = property(
        lambda self: self.control_list,
        lambda self, x: setattr(self, 'control_list', x)
    )


class CardSelectionPanel(Panel):
    NONE = 0
    SINGLE = 1
    MULTIPLE = 2

    def __init__(self, selection_mode=0, *a, **k):
        self.selection_mode = selection_mode
        self.lbls = pyglet.graphics.Batch()
        self.selection = []
        Panel.__init__(self, width=1, height=1, *a, **k)

    '''
    card_lists = [
        (cl_name, cl),
        ...
    ]
    '''
    def init(self, card_lists, compat=True, multiline=False):
        name_width = 100 if any(cl[0] for cl in card_lists) else 0
        y = 40
        h = y + 10
        w = name_width + 6*93.0+30
        i = 0
        for name, cl in reversed(card_lists):
            if not cl:
                if compat: continue
                if multiline:
                    i += 1
                    h += 125

            for sindex in reversed(xrange(0, len(cl), 6)):
                if multiline:
                    cat = cl[sindex:sindex+6]
                else:
                    cat = cl

                ca = DropCardArea(
                    parent=self,
                    x=name_width, y=y+145*i,
                    fold_size=6,
                    width=6*93, height=145,
                )

                def register_events(cs):
                    @cs.event
                    def on_mouse_click(*v, **k):
                        self.toggle_selection(cs)

                    @cs.event
                    def on_mouse_dblclick(*v, **k):
                        self.dispatch_event('on_confirm', cs)

                for c in cat:
                    cs = CardSprite(c, parent=ca)
                    cs.associated_card = c
                    register_events(cs)

                ca.update()
                i += 1
                h += 145

                if not multiline: break

            name and Label(
                text=name, x=30, y=y+62+145*(i-1), font_size=12,
                color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 130),
                anchor_x='left', anchor_y='center', batch=self.lbls,
            )

        p = self.parent
        self.x, self.y = (p.width - w)//2, (p.height - h)//2
        self.width, self.height = w, h
        self.update()

        btn = ImageButton(
            L('c-buttons-close_blue'),
            parent=self,
            anchor_x='right', anchor_y='top',
            x=w-20, y=h-20,
        )

        @btn.event
        def on_click():
            self.delete()

    def toggle_selection(self, cs):
        if not cs.selected:
            mode = self.selection_mode
            if mode == CardSelectionPanel.NONE: return
            if mode == CardSelectionPanel.SINGLE:
                for c in self.selection:
                    c.selected = False
                self.selection[:] = []

            self.selection.append(cs)
            cs.selected = True

        else:
            self.selection.remove(cs)
            cs.selected = False

        self.dispatch_event('on_selection_change')

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()

CardSelectionPanel.register_event_type('on_confirm')
CardSelectionPanel.register_event_type('on_selection_change')


class ShownCardPanel(CardSelectionPanel):
    current = None

    def __init__(self, character, *a, **k):
        self.character = character
        ShownCardPanel.current = self

        card_lists = [
            (CardList.ui_meta.lookup[cat.type], cat)
            for cat in character.showncardlists
        ]

        CardSelectionPanel.__init__(self, zindex=5, *a, **k)
        self.init(card_lists)

    def delete(self):
        super(ShownCardPanel, self).delete()
        ShownCardPanel.current = None


class _CharacterFigure(Control):
    def __init__(self, texture, prompt, parent, *a, **k):
        self.texture = texture
        self.prompt = prompt

        width = texture.width
        height = texture.height

        x = (parent.width - width) // 2
        y = (parent.height - height) // 2

        self._x = x
        self._y = y

        Control.__init__(self, *a, x=x, y=y, width=width, height=height, parent=parent, zindex=999999, **k)

        ta = TextArea(
            parent=self,
            # font_size=12,
            x=2, y=2, width=width, height=100,
        )

        ta.append(prompt)
        h = ta.content_height
        ta.height = h
        self.ta_height = h

    def draw(self):
        glColor3f(1, 1, 1)
        self.texture.blit(0, 0)
        glColor4f(1, 1, 1, 0.65)
        glRectf(0, 0, self.width, self.ta_height)
        self.draw_subcontrols()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, v):
        pass

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, v):
        pass


class GameCharacterPortrait(Frame):
    dropped = False
    fleed = False
    actor_frame = None
    turn_frame = None

    def __init__(self, x=0.0, y=0.0, color=Colors.blue, tag_placement='me', *args, **kwargs):
        self.bg = None
        self.character = None
        self._color = color
        self._disabled = False
        self._last_balloon = None
        self.player = None
        self._selected = False
        self.taganims = []
        self.tag_placement = tag_placement

        Frame.__init__(
            self, width=149, height=195,
            bot_reserve=20, color=color,
            thin_shadow=True,
            **kwargs
        )
        self.balloon = BalloonPrompt(self, self.balloon_show)

        self.view = view = self.parent
        self.x, self.y = x, y

        self.charname_lbl = self.add_label(
            u'', 7, self.height-30,
            width=16, multiline=True,
            font_size=9,
            anchor_x='left', anchor_y='top',
            color=(255, 255, 255, 255),
            shadow=(1, 0, 0, 0, 179),
        )

        self.portcard_area = PortraitCardArea(
            parent=view,
            x=self.x, y=self.y,
            width=self.width, height=self.height,
            zindex=100,
        )
        self.equipcard_area = EquipCardArea(
            view=view, parent=self, x=3, y=6,
        )

        w, h = self.width, self.height

        tbl = view.game.ui_meta.identity_table
        colortbl = view.game.ui_meta.identity_color
        conf = [(tbl[k], getattr(Colors, colortbl[k]), k) for k in tbl]

        self.identity_btn = b = OptionButton(
            conf=conf, default=0, parent=self,
            x=w-42-4, y=h-24-10-18,
            width=42, height=18,
        )

        @b.event
        def on_value_changed(v):
            self.set_color(b.color)

        def tagarrange_bottom():
            x, y = self.x, self.y
            w = self.width
            x += w + 1
            y -= 27
            for a in self.taganims:  # they are pyglet.sprite.Sprite instances
                x -= 27
                a.set_position(x, y)

        def tagarrange_me():
            x, y = self.x, self.y
            w = self.width
            x += w + 6
            y += 142
            for a in self.taganims:  # they are pyglet.sprite.Sprite instances
                a.set_position(x, y)
                x += 27

        def tagarrange_right():
            x, y = self.x, self.y
            w = self.width
            x += w + 3
            y += 1
            for a in self.taganims:  # they are pyglet.sprite.Sprite instances
                a.set_position(x, y)
                y += 27

        def tagarrange_left():
            x, y = self.x, self.y
            x -= 28
            y += 1
            for a in self.taganims:  # they are pyglet.sprite.Sprite instances
                a.set_position(x, y)
                y += 27

        self._tagarrange_funcs = {
            'bottom': tagarrange_bottom,
            'me': tagarrange_me,
            'left': tagarrange_left,
            'right': tagarrange_right,
        }

        showncard_btn = ImageButton(
            L('c-buttons-port_showncard'),
            parent=self,
            x=self.width - 22, y=90,
        )

        @showncard_btn.event  # noqa
        def on_click():
            p = self.character
            if not p: return
            if not p.showncardlists: return  # before the 'real' game_start
            last = ShownCardPanel.current
            if last:
                last.delete()
                if last.character is p:
                    return

            ShownCardPanel(p, parent=self.view)

    def update(self):
        p = self.player
        if not p: return

        nick = u"<%s>" % p.account.username
        if self.dropped:
            if self.fleed:
                prefix = u'(逃跑)'
            else:
                prefix = u'(掉线)'

            nick = prefix + nick

        self.caption = nick
        char = self.character

        if char:
            meta = char.ui_meta
            self.bg = L(meta.port_image)
            self.update_bg()
            self.set_charname(meta.char_name)
            if self._last_balloon != meta.description:
                self.balloon.set_balloon(meta.description, (2, 74, 145, 96))
                self._last_balloon = meta.description

        self.bot_reserve = 74
        self.gray_tex = None
        Frame.update(self)
        self.update_position()
        self.update_color()
        self.tagarrange()

    def balloon_show(self):
        try:
            meta = self.character.ui_meta
            figure_image = L(meta.figure_image)
        except:
            return self.balloon.balloon_show()

        try:
            figure_image_alter = L(meta.figure_image_alter)
            if figure_image_alter.decrypted:
                figure_image = figure_image_alter

        except:
            pass

        return _CharacterFigure(
            figure_image,
            meta.description,
            parent=self.parent,
        )

    @property
    def color(self):
        if not self.character:
            return self._color

        if self.character.dead:
            return Colors.gray

        return self._color

    @property
    def bg(self):
        if not self.character:
            return self._bg

        if self.character.dead:
            return self._bg.grayed

        return self._bg

    @bg.setter
    def bg(self, val):
        self._bg = val

    def _fill_batch(self, batch):
        Frame._fill_batch(self, batch)
        self._gcp_framevlist = batch.add(16, GL_QUADS, self.frame_group, 'c4B', 'v2f')
        self._highlight_disabled = batch.add(4, GL_QUADS, self.top_group, 'c4B', 'v2f')
        self._highlight = batch.add(4, GL_QUADS, self.top_group, 'c4B', 'v2f')

        self.selected = self.selected
        self.disabled = self.disabled
        GameCharacterPortrait.update_position(self)
        GameCharacterPortrait.update_color(self)

    def set_postion(self, x, y):
        Frame.set_position(self, x, y)
        GameCharacterPortrait.update_position(self)

    def update_position(self):
        Frame.update_position(self)
        w, h = self.width, self.height
        ax, ay = self.abs_coords()
        self._gcp_framevlist.vertices[:] = flatten([
            rectv2f(2, 2, w-4, 54-2, ax, ay),  # equip box
            rrectv2f(2.5, 2.5, 4*36, 52, ax, ay),  # equip box border
            rectv2f(w-2-32, 66, 32, 22, ax, ay),  # cardnum box
            rrectv2f(w-2-32, 66, 32, 22, ax, ay),  # cardnum box border
        ])

        full = rectv2f(0, 0, w, h, ax, ay)
        self._highlight_disabled.vertices[:] = full
        self._highlight.vertices[:] = full

        if self.actor_frame:
            self.actor_frame.set_position(self.x - 6, self.y - 4)

        if self.turn_frame:
            self.turn_frame.set_position(self.x - 6, self.y - 4)

    def set_color(self, color):
        Frame.set_color(self, color)
        GameCharacterPortrait.update_color(self)

    def update_color(self):
        Frame.update_color(self)
        C = Colors.get4i
        c = self.color
        heavy, light = C(c.heavy), C(c.light)
        self._gcp_framevlist.colors = flatten([
            [255, 255, 255, 255] * 4,  # equip box
            [heavy] * 4,  # equip box border
            [light] * 4,  # cardnum box
            [heavy] * 4,  # cardnum box border
        ])

    def set_charname(self, char_name):
        self.charname_lbl.text = char_name

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, val):
        self._disabled = val
        color = (0, 0, 0, 128) if val else (0, 0, 0, 0)
        self._highlight_disabled.colors[:] = color * 4

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, val):
        self._selected = val
        color = (255, 255, 204, 153) if val else (0, 0, 0, 0)
        self._highlight.colors[:] = color * 4

    @staticmethod
    def batch_draw_status(gcps):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        vertices = []
        for port in gcps:
            char = port.character
            if not char: continue

            hp, hp_bg = L('thb-hp'), L('thb-hp_bg')
            if char.dead:
                hp = hp.grayed
                hp_bg = hp_bg.grayed

            # hp bar
            w = hp.width
            x, y = port.x, port.y
            for i in xrange(char.maxlife):
                vertices.extend(
                    hp_bg.get_t4f_v4f_vertices(5+x+i*w, 56+y)
                )

            for i in xrange(max(char.life, 0)):
                vertices.extend(
                    hp.get_t4f_v4f_vertices(5+x+i*w, 56+y)
                )

        nums = L('thb-num')
        for port in gcps:
            x, y, w = port.x, port.y, port.width
            char = port.character
            if not char: continue

            n = len(char.cards) + len(char.showncards)
            seq = str(n)
            ox = (32 - len(seq)*14)//2
            for i, ch in enumerate(seq):
                n = ord(ch) - ord('0')
                # x, y = w - 34 + ox + i*14, 68
                vertices.extend(nums[n].get_t4f_v4f_vertices(
                    x + w - 34 + ox + i*14,
                    y + 68
                ))

        if vertices:
            with nums[0].owner:
                n = len(vertices)
                buf = (GLfloat*n)()
                buf[:] = vertices
                glInterleavedArrays(GL_T4F_V4F, 0, buf)
                glDrawArrays(GL_QUADS, 0, n/8)

        glPopClientAttrib()

    @staticmethod
    def batch_draw(gcps):
        glPushMatrix()
        glLoadIdentity()
        Frame.batch_draw(gcps)
        GameCharacterPortrait.batch_draw_status(gcps)
        glPopMatrix()
        cl = []
        map(cl.extend, [p.control_list for p in gcps])
        Control.do_draw(cl)

    @property
    def zindex(self):
        return 0

    @zindex.setter
    def zindex(self, val):
        pass

    def delete(self):
        Frame.delete(self)
        self.portcard_area.delete()

    def tagarrange(self):
        self._tagarrange_funcs[self.tag_placement]()

    def on_game_event(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, actions.RevealIdentity):
            act = arg
            g = Game.getgame()
            me = g.me
            if (act.target in (self.player, self.character)) and (me in act.to if isinstance(act.to, list) else me is act.to):
                btn = self.identity_btn
                btn.value = act.target.identity.type
                btn.state = Button.DISABLED
                btn.update()
                # self.update()

        elif evt_type == 'switch_character':
            p = arg
            if p.player is self.player:
                self.character = p
                self.update()

    def animate_to(self, x, y):
        tx = SineInterp(self.x, x, 1)
        ty = SineInterp(self.y, y, 1)
        pca = self.portcard_area

        def _update(dt):
            if tx.finished:
                pyglet.clock.unschedule(_update)
                self.identity_btn.update()
                return

            pca.x = x
            pca.y = y
            self.set_position(tx.value, ty.value)

        pyglet.clock.schedule_interval_soft(_update, 1/60.0)
