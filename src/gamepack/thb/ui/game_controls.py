# -*- coding: utf-8 -*-
from client.ui.base import Control, ui_message
from client.ui.controls import *
from client.ui import resource as common_res
import resource as game_res
from client.ui import shaders
from game.autoenv import Game
from .. import actions

from utils import DisplayList, partition, flatten

import pyglet

HAVE_FBO = pyglet.gl.gl_info.have_extension('GL_EXT_framebuffer_object')

class CardSprite(Control, BalloonPrompt):
    x = InterpDesc('_x')
    y = InterpDesc('_y')
    back_scale = InterpDesc('_bs')
    question_scale = InterpDesc('_qs')
    ftanim_alpha = InterpDesc('_fta')
    ftanim_cardalpha = InterpDesc('_ftca')
    shine_alpha = InterpDesc('_shine_alpha')
    alpha = InterpDesc('_alpha')
    img_cardq = game_res.card_question
    img_cardh = game_res.card_hidden
    width, height = 91, 125

    def __init__(self, card, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)

        self._w, self._h = 91, 125
        self.shine = False
        self.gray = False
        self.x, self.y,  = x, y
        self.shine_alpha = 0.0
        self.alpha = 1.0
        self.card = card

        self.ft_anim = False

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
                if n: vertices += game_res.cardnumbers[s%2*13 + n-1].get_t2c4n3v3_vertices(c, ax+5, ay+105)
                if s: vertices += game_res.suit[s-1].get_t2c4n3v3_vertices(c, ax+6, ay+94)

                c = (1, 1, 1, aa)

                if qs:
                    vertices += game_res.card_question.get_t2c4n3v3_vertices(c, ax+(1-qs)*45, ay, 0, qs*91)

                if bs:
                    vertices += game_res.card_hidden.get_t2c4n3v3_vertices(c, ax+(1-bs)*45, ay, 0, bs*91)
            else:
                a = cs.alpha
                if cs.gray:
                    c = (.66, .66, .66, a)
                else:
                    c = (1., 1., 1., a)
                vertices += cs.img.get_t2c4n3v3_vertices(c, ax, ay)
                if cs.card.resides_in.type == 'showncard':
                    vertices += game_res.card_showncardtag.get_t2c4n3v3_vertices(c, ax, ay)

                n, s = cs.number, cs.suit
                if n: vertices += game_res.cardnumbers[s%2*13 + n-1].get_t2c4n3v3_vertices(c, ax+5, ay+105)
                if s: vertices += game_res.suit[s-1].get_t2c4n3v3_vertices(c, ax+6, ay+94)

                vertices += game_res.card_shinesoft.get_t2c4n3v3_vertices(
                    (1., 1., 1., cs.shine_alpha), ax-6, ay-6
                )

        if vertices:
            n = len(vertices)
            buf = (GLfloat*n)()
            buf[:] = vertices
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glInterleavedArrays(GL_T2F_C4F_N3F_V3F, 0, buf)
            with game_res.card_atlas.texture:
                glDrawArrays(GL_QUADS, 0, n/12)
            glPopClientAttrib()

        glPopMatrix()

    def update(self):
        card = self.card
        meta = card.ui_meta

        self.img = meta.image

        self.number, self.suit = card.number, card.suit

        t = getattr(meta, 'description', None)
        if t: self.init_balloon(t)

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

    '''
    def draw(self):
        glColor4f(1,1,1,1)
        if not self.control_list: return
        with game_res.card_atlas.texture:
            for cs in self.control_list:
                glPushMatrix()
                glTranslatef(cs.x, cs.y, 0)
                cs.draw_vertices()
                glPopMatrix()
    '''

    batch_draw = cardarea_batch_draw

    def update(self):
        fsz = self.fold_size
        n = len(self.control_list)
        width = min(fsz*93.0+42, n*93.0)
        step = (width - 91)/(n-1) if n > 1 else 0
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
        self.dispatch_event('on_selection_change')

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        if c:
            self.toggle(c, 0.1)

    cards = property(
        lambda self: self.control_list,
        lambda self, x: setattr(self, 'control_list', x)
    )

HandCardArea.register_event_type('on_selection_change')

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

    '''
    def draw(self):
        glColor4f(1,1,1,1)
        if not self.control_list: return
        with game_res.card_atlas.texture:
            for cs in self.control_list:
                glPushMatrix()
                glTranslatef(cs.x, cs.y, 0)
                cs.draw_vertices()
                glPopMatrix()'''

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
    img_ray = common_res.ray
    scale = InterpDesc('_scale')
    alpha = InterpDesc('_alpha')

    def __init__(self, x0, y0, x1, y1, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        from math import sqrt, atan2, pi
        self.x, self.y = x0, y0
        dx, dy = x1 - x0, y1 - y0
        scale = sqrt(dx*dx+dy*dy) / self.img_ray.width
        self.angle = atan2(dy, dx) / pi * 180
        self.scale = SineInterp(0.0, scale, 0.4)
        self.alpha = ChainInterp(
            FixedInterp(1.0, 1),
            CosineInterp(1.0, 0.0, 0.5),
            on_done=lambda self, desc: self.delete()
        )

    def draw(self):
        glPushMatrix()
        glRotatef(self.angle, 0., 0., 1.)
        glScalef(self.scale, 1., 1.)
        glTranslatef(0., -self.img_ray.height/2, 0.)
        glColor4f(1., 1., 1., self.alpha)
        self.img_ray.blit(0,0)
        glPopMatrix()

    def hit_test(self, x, y):
        return False

class SkillSelectionBox(Control):
    class SkillButton(Button):
        def __init__(self, enable, sid, *a, **k):
            Button.__init__(self, width=71, height=20, *a, **k)
            self.selected = False
            self.state = Button.NORMAL if enable else Button.DISABLED
            self.color = Colors.blue
            self.sid = sid
            self.update()

        def on_click(self):
            buttons = self.parent.buttons
            if self.selected:
                self.parent.selection.remove(self.sid)
                self.color = Colors.blue
                self.selected = False
                self.update()
            else:
                self.color = Colors.orange
                self.update()
                self.parent.selection.append(self.sid)
                self.selected = True

            self.parent.parent.dispatch_event('on_selection_change')

    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.selection = []

    def set_skills(self, lst):
        # lst = (('name1', sid1, enable), ('name2', sid2, enable), ...)
        y = self.height
        for b in self.buttons[:]:
            b.delete()

        assert not self.buttons

        for nam, sid, enable in lst:
            y -= 22
            SkillSelectionBox.SkillButton(enable, sid, nam, parent=self, x=0, y=y)

        self.selection = []

    @property
    def buttons(self):
        return self.control_list

    def get_selected_index(self):
        return self.selection

    def draw(self):
        self.draw_subcontrols()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

class SmallCardSprite(Control, BalloonPrompt):
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

        self.img = card.ui_meta.image_small
        self.init_balloon(card.ui_meta.description)

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

            ssuit = game_res.smallsuit
            snum = game_res.smallnum

            if n == 10: # special case
                #g[0].blit(1+g[0].vertices[0], 33+g[0].vertices[1])
                #g[1].blit(5+g[1].vertices[0], 33+g[1].vertices[1])
                vertices += snum[s%2*14 + 10].get_t4f_v4f_vertices(ax-1, ay+31)
                vertices += snum[s%2*14 + 0].get_t4f_v4f_vertices(ax+3, ay+31)
            else:
                vertices += snum[s%2*14 + n].get_t4f_v4f_vertices(ax+1, ay+31)
            vertices += ssuit[s-1].get_t4f_v4f_vertices(ax+1, ay+22)

            if cs.selected:
                vertices += game_res.scardframe_selected.get_t4f_v4f_vertices(ax, ay)
            else:
                vertices += game_res.scardframe_normal.get_t4f_v4f_vertices(ax, ay)

        n = len(vertices)
        buf = (GLfloat*n)()
        buf[:] = vertices
        glColor3f(1., 1., 1.)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glInterleavedArrays(GL_T4F_V4F, 0, buf)
        with game_res.card_atlas.texture:
            glDrawArrays(GL_QUADS, 0, n/8)

        glPopClientAttrib()
        glPopMatrix()

class EquipCardArea(Control):
    def __init__(self, fold_size=4, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.width, self.height = 35*4, 46
        self.fold_size = fold_size
        self.selectable = False

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
        step = int((width - 34)/(n-1)) if n > 1 else 0
        for i, c in enumerate(self.control_list):
            c.zindex = i
            c.x = SineInterp(c.x, 2 + step * i, 0.4)
            c.y = SineInterp(c.y, 0, 0.4)

    def on_mouse_click(self, x, y, button, modifier):
        if not self.selectable: return
        c = self.control_frompoint1(x, y)
        if c:
            s = c.selected = not c.selected
            self.dispatch_event('on_selection_change')

    def clear_selection(self):
        for c in self.control_list:
            c.selected = False
        self.dispatch_event('on_selection_change')

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    cards = property(
        lambda self: self.control_list,
        lambda self, x: setattr(self, 'control_list', x)
    )
EquipCardArea.register_event_type('on_selection_change')

class ShownCardPanel(Panel):
    from ..cards.base import CardList
    lookup = {
        'handcard': u'手牌区',
        'showncard': u'明牌区',
        'equips': u'装备区',
        'fatetell': u'判定区',
        'bomb': u'BOMB'
    }

    current = None
    def __init__(self, player, *a, **k):
        self.player = player
        ShownCardPanel.current = self

        categories = player.showncardlists

        h = 30 + len(categories)*145 + 10
        w = 100 + 6*93.0+30
        self.lbls = lbls = pyglet.graphics.Batch()

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)

        y = 30

        i = 0
        for cat in reversed(categories):

            ShadowedLabel(
                text=self.lookup[cat.type], x=30, y=y+62+145*i, font_size=12,
                color=(255, 255, 160, 255), shadow_color=(0, 0, 0, 130),
                anchor_x='left', anchor_y='center', batch=lbls,
            )
            ca = DropCardArea(
                parent=self,
                x=100, y=y+145*i,
                fold_size=6,
                width=6*93, height=125,
            )
            for c in cat:
                cs = CardSprite(c, parent=ca)
                cs.associated_card = c
            ca.update()
            i += 1

        p = self.parent
        self.x, self.y = (p.width - w)//2, (p.height - h)//2
        self.width, self.height = w, h
        self.update()

        btn = ImageButton(
            common_res.buttons.close_blue,
            parent=self,
            x=w-20, y=h-20,
        )

        @btn.event
        def on_click():
            self.delete()

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()

    def delete(self):
        Panel.delete(self)
        ShownCardPanel.current = None


class GameCharacterPortrait(Frame, BalloonPrompt):
    dropped = False
    fleed = False
    actor_frame = None
    turn_frame = None

    def __init__(self, x=0.0, y=0.0, color=Colors.blue, tag_placement='me', *args, **kwargs):
        self.player = None
        self._disabled = False
        self._selected = False
        self.taganims = []
        self.tag_placement = tag_placement
        self._color = color
        self.bg = None
        self._last_balloon = None

        Frame.__init__(
            self, width=149, height=195,
            bot_reserve=20, color=color,
            thin_shadow=True,
            **kwargs
        )
        self.x, self.y = x, y

        self.charname_lbl = self.add_label(
            u'', 7, self.height-30,
            width=16, multiline=True,
            font_size=9,
            anchor_x='left', anchor_y='top',
            color=(255, 255, 255, 255),
            shadow='thin', shadow_color=(0, 0, 0, 179),
        )

        from .view import THBattleUI
        v = self.parent
        while not isinstance(v, THBattleUI):
            v = v.parent
        self.view = v

        self.portcard_area = PortraitCardArea(
            parent=self.view,
            x=self.x, y=self.y,
            width=self.width, height=self.height,
            zindex=100,
        )
        self.equipcard_area = EquipCardArea(
            parent=self,
            x=3, y=6,
        )

        w, h = self.width, self.height

        self.identity_btn = b = Button(
            u'？', parent = self,
            x=w-42-4, y=h-24-10-18,
            width=42, height=18,
        )

        self.cur_idtag = 0

        @b.event
        def on_click():
            g = Game.getgame()
            tbl = g.ui_meta.identity_table
            colortbl = g.ui_meta.identity_color
            keys = tbl.keys()
            try:
                i = (keys.index(self.cur_idtag) + 1) % len(keys)
            except ValueError:
                i = 0
            next = keys[i]
            b.caption = tbl[next]
            color = getattr(Colors, colortbl[next])
            b.color = color
            self.set_color(color)
            b.update()
            self.update()
            self.cur_idtag = next

        @self.equipcard_area.event
        def on_selection_change():
            self.view.dispatch_event('on_selection_change')

        def tagarrange_bottom():
            x, y = self.x, self.y
            w, h = self.width, self.height
            x += w + 1
            y -= 27
            for a in self.taganims: # they are pyglet.sprite.Sprite instances
                x -= 27
                a.set_position(x, y)

        def tagarrange_me():
            x, y = self.x, self.y
            w, h = self.width, self.height
            x += w + 6
            y += 142
            for a in self.taganims: # they are pyglet.sprite.Sprite instances
                a.set_position(x, y)
                x += 27

        def tagarrange_right():
            x, y = self.x, self.y
            w, h = self.width, self.height
            x += w + 3
            y += 1
            for a in self.taganims: # they are pyglet.sprite.Sprite instances
                a.set_position(x, y)
                y += 27

        def tagarrange_left():
            x, y = self.x, self.y
            w, h = self.width, self.height
            x -= 28
            y += 1
            for a in self.taganims: # they are pyglet.sprite.Sprite instances
                a.set_position(x, y)
                y += 27

        self._tagarrange_funcs = {
            'bottom': tagarrange_bottom,
            'me': tagarrange_me,
            'left': tagarrange_left,
            'right': tagarrange_right,
        }

        showncard_btn = ImageButton(
            common_res.buttons.port_showncard,
            parent=self,
            x=self.width - 22, y=90,
        )

        @showncard_btn.event
        def on_click():
            p = self.player
            if not p: return
            if not hasattr(p, 'showncardlists'): return # before the 'real' game_start
            last = ShownCardPanel.current
            if last:
                last.delete()
                if last.player is p:
                    return
            ShownCardPanel(p, parent=self.view)

    def update(self):
        p = self.player
        if not p: return

        nick = p.account.username
        if self.dropped:
            if self.fleed:
                prefix = u'(逃跑)'
            else:
                prefix = u'(掉线)'

            nick = prefix + nick

        self.caption = nick
        meta = getattr(p, 'ui_meta', None)

        if meta:
            self.bg = meta.port_image
            self.update_bg()
            self.set_charname(meta.char_name)
            if self._last_balloon != meta.description:
                self.init_balloon(meta.description, (2, 74, 145, 96))
                self._last_balloon = meta.description

        self.bot_reserve=74
        self.gray_tex = None
        Frame.update(self)
        self.update_position()
        self.update_color()

    @property
    def color(self):
        if not self.player:
            return self._color

        dead = getattr(self.player, 'dead', False)
        if dead:
            return Colors.gray
        
        return self._color

    @property
    def bg(self):
        if not self.player:
            return self._bg

        dead = getattr(self.player, 'dead', False)

        if dead:
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
        heavy = C(c.heavy); light = C(c.light)
        self._gcp_framevlist.colors = flatten([
            [255, 255, 255, 255] * 4,  # equip box
            [heavy] * 4,  # equip box border
            [light] * 4,  # cardnum box
            [heavy] * 4,  # cardnum box border
        ])

    def set_charname(self, char_name):
        s = u'\u200b'.join(char_name)
        self.charname_lbl.text = s
        self.charname_lbl._shadow.text = s

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
            p = port.player
            if not getattr(p, 'ui_meta', False): continue

            hp = game_res.hp; hp_bg = game_res.hp_bg
            if getattr(p, 'dead', False):
                hp = hp.grayed
                hp_bg = hp_bg.grayed

            # hp bar
            w = hp.width
            x = port.x; y = port.y
            for i in xrange(getattr(p, 'maxlife', 0)):
                vertices.extend(
                    hp_bg.get_t4f_v4f_vertices(5+x+i*w, 56+y)
                )

            for i in xrange(max(getattr(p, 'life', 0), 0)):
                vertices.extend(
                    hp.get_t4f_v4f_vertices(5+x+i*w, 56+y)
                )

        nums = game_res.num
        for port in gcps:
            x, y, w, h = port.x, port.y, port.width, port.height
            p = port.player
            try:
                n = len(p.cards) + len(p.showncards)
                seq = str(n)
                ox = (32 - len(seq)*14)//2
                for i, ch in enumerate(seq):
                    n = ord(ch) - ord('0')
                    #x, y = w - 34 + ox + i*14, 68
                    vertices.extend(nums[n].get_t4f_v4f_vertices(
                        x + w - 34 + ox + i*14,
                        y + 68
                    ))
            except AttributeError as e:
                pass

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

    def on_message(self, _type, *args):
        if _type == 'evt_action_after' and isinstance(args[0], actions.RevealIdentity):
            act = args[0]
            g = Game.getgame()
            me = g.me
            if (act.target is self.player) and (me in act.to if isinstance(act.to, list) else me is act.to):
                btn = self.identity_btn
                tbl = g.ui_meta.identity_table
                colortbl = g.ui_meta.identity_color
                color = getattr(Colors, colortbl[act.target.identity.type])
                btn.caption = tbl[act.target.identity.type]
                btn.state = Button.DISABLED
                btn.update()
                self.set_color(color)
                # self.update()

    def animate_to(self, x, y):
        tx = SineInterp(self.x, x, 1)
        ty = SineInterp(self.y, y, 1)
        pca = self.portcard_area
        def _update(dt):
            if tx.finished:
                pyglet.clock.unschedule(_update)
                return

            pca.x = x
            pca.y = y
            self.set_position(tx.value, ty.value)

        pyglet.clock.schedule_interval_soft(_update, 1/60.0)
