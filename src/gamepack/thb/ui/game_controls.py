# -*- coding: utf-8 -*-
from client.ui.base import Control, message as ui_message
from client.ui.controls import *
from client.ui import resource as common_res
from client.ui import shaders

class CardSprite(Control, BalloonPrompt):
    x = InterpDesc('_x')
    y = InterpDesc('_y')
    back_scale = InterpDesc('_bs')
    question_scale = InterpDesc('_qs')
    ftanim_alpha = InterpDesc('_fta')
    ftanim_cardalpha = InterpDesc('_ftca')
    shine_alpha = InterpDesc('_shine_alpha')
    alpha = InterpDesc('_alpha')
    img_shinesoft = common_res.card_shinesoft
    img_cardq = common_res.card_question
    img_cardh = common_res.card_hidden
    width, height = 91, 125
    auxfbo = Framebuffer()
    def __init__(self, card, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 91, 125
        self.shine = False
        self.gray = False
        self.x, self.y,  = x, y
        self.shine_alpha = 0.0
        self.alpha = 1.0

        meta = card.ui_meta

        self.img = meta.image

        self.tex = pyglet.image.Texture.create(91, 125)

        self.number, self.suit = card.number, card.suit
        self.ft_anim = False

        t = getattr(meta, 'description', None) # FOR DEBUG
        if t:
            self.init_balloon(t)

        self.update()

    def draw(self):
        if self.ft_anim:
            qs = self.question_scale
            bs = self.back_scale
            aa = self.ftanim_alpha
            ca = self.ftanim_cardalpha
            if self.gray:
                glColor4f(.66, .66, .66, ca)
            else:
                glColor4f(1., 1., 1., ca)
            self.tex.blit(0, 0)

            glColor4f(1, 1, 1, aa)

            if qs:
                self.img_cardq.blit((1-qs)*45, 0, 0, qs*91)

            if bs:
                self.img_cardh.blit((1-bs)*45, 0, 0, bs*91)
        else:
            a = self.alpha
            if self.gray:
                glColor4f(.66, .66, .66, a)
            else:
                glColor4f(1., 1., 1., a)
            self.tex.blit(0, 0)


        glColor4f(1., 1., 1., self.shine_alpha)
        self.img_shinesoft.blit(-6, -6)

    def update(self):
        fbo = self.auxfbo
        with fbo:
            fbo.texture = self.tex
            glColor3f(1, 1, 1)
            self.img.blit(0, 0)
            n, s = self.number, self.suit
            glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE)
            if n: common_res.cardnumbers[s%2, n-1].blit(5, 105)
            if s: common_res.suit[s-1].blit(6, 94)

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

class HandCardArea(Control):
    def __init__(self, fold_size=5, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.fold_size = fold_size

    def draw(self):
        glColor4f(1,1,1,1)
        self.draw_subcontrols()

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

    def draw(self):
        self.draw_subcontrols()

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

    def draw(self):
        glColor4f(1,1,1,1)
        self.draw_subcontrols()

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
        def __init__(self, sid, *a, **k):
            Button.__init__(self, width=71, height=20, *a, **k)
            self.selected = False
            self.state = Button.DISABLED
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
        # lst = (('name1', sid1), ('name2', sid2), ...)
        y = self.height
        for b in self.buttons[:]:
            b.delete()

        assert not self.buttons

        for nam, sid in lst:
            y -= 22
            SkillSelectionBox.SkillButton(sid, nam, parent=self, x=0, y=y)

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
    auxfbo = Framebuffer()
    def __init__(self, card, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 33, 46
        self.x, self.y = x, y
        self.selected = False
        self.hover = False

        bg = card.ui_meta.image_small
        from pyglet.image import Texture
        img = Texture.create(bg.width, bg.height)
        fbo = self.auxfbo

        f = pyglet.font.load('AncientPix', size=9)

        ssuit = common_res.smallsuit
        with fbo:
            fbo.texture = img
            glColor3f(1, 1, 1)
            bg.blit(0, 0)
            if card.suit % 2:
                glColor3f(0, 0, 0)
            else:
                glColor3f(1, 0, 0)

            with shaders.FontShadow as fs:
                fs.uniform.shadow_color = (1.0, 1.0, 1.0, 0.7)
                if card.number == 10: # special case
                    g = f.get_glyphs('10')
                    g[0].blit(1+g[0].vertices[0], 33+g[0].vertices[1])
                    g[1].blit(5+g[1].vertices[0], 33+g[1].vertices[1])
                else:
                    g = f.get_glyphs(' A23456789!JQK'[card.number])[0]
                    g.blit(3+g.vertices[0], 33+g.vertices[1])
                ssuit[card.suit-1].blit(1, 24)
        self.img = img
        self.init_balloon(card.ui_meta.description)

    def draw(self):
        glColor3f(1., 1., 1.)
        self.img.blit(0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        if self.selected:
            glColor3f(0, 1, 0)
        else:
            glColor4f(0, 0, 1, 0.5)

        glRectf(0, 0, 33, 46)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

class EquipCardArea(Control):
    def __init__(self, fold_size=4, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.width, self.height = 35*4, 46
        self.fold_size = fold_size
        self.selectable = False

    def draw(self):
        glColor4f(1,1,1,1)
        self.draw_subcontrols()

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
    current = None
    def __init__(self, player, *a, **k):
        self.player = player
        ShownCardPanel.current = self
        h = 30 + 145 + 10
        w = 100 + 6*93.0 + 30

        self.lbl = pyglet.text.Label(
            text=u'明牌区',
            font_name = 'AncientPix', font_size=12,
            color=(255, 255, 160, 255),
            x=30, y=30+62,
            anchor_x='left', anchor_y='center',
        )

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)
        p = self.parent
        self.x, self.y = (p.width - w)//2, (p.height - h)//2
        self.width, self.height = w, h
        self.update()

        ca = DropCardArea(
            parent=self,
            x=100, y=30,
            fold_size=6,
            width=6*93, height=125,
        )
        for c in player.showncards:
            cs = CardSprite(c, parent=ca)
        ca.update()

        closebtn = ImageButton(
            common_res.buttons.close_blue,
            parent=self,
            x=w-20, y=h-20
        )
        @closebtn.event
        def on_click():
            self.delete()

    def blur_update(self):
        Panel.blur_update(self)
        fbo = self.auxfbo
        with fbo:
            fbo.texture = self.tex1
            with shaders.FontShadow as fs:
                fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.9)
                self.lbl.draw()

    def delete(self):
        Panel.delete(self)
        ShownCardPanel.current = None

class GameCharacterPortrait(Dialog, BalloonPrompt):
    dropped = False

    def __init__(self, color=Colors.blue, tag_placement='me', *args, **kwargs):
        self.selected = False
        self.player = None
        self.disabled = False
        self.taganims = []
        self.tag_placement = tag_placement

        Dialog.__init__(
            self, width=149, height=195,
            bot_reserve=20, color=color,
            shadow_thick=1,
            **kwargs
        )
        self.no_move = True
        self.btn_close.state = Button.DISABLED
        self.portcard_area = PortraitCardArea(
            parent=self.parent,
            x=self.x, y=self.y,
            width=self.width, height=self.height,
            zindex=100,
        )
        self.equipcard_area = EquipCardArea(
            parent=self,
            x=3, y=6,
            manual_draw=True,
        )

        self.grayed_tex = None

        #self.prompt_area = PromptControl(
        #    parent=self, x=2, y=74, width=145, height=96, zindex=-1,
        #)

        @self.equipcard_area.event
        def on_selection_change():
            self.parent.dispatch_event('on_selection_change')

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
            if not hasattr(p, 'showncards'): return # before the 'real' game start
            last = ShownCardPanel.current
            if last:
                last.delete()
                if last.player is p:
                    return
            ShownCardPanel(p, parent=self.parent)

    def update(self):
        p = self.player
        if not p: return

        nick = p.username
        if self.dropped: nick = u'(离开)' + nick
        self.caption = nick
        try:
            meta = p.ui_meta

        except AttributeError:
            # before girls chosen
            Dialog.update(self)
            return

        self.bg = meta.port_image
        self.init_balloon(meta.description, (2, 74, 145, 96))

        self.bot_reserve=74
        Dialog.update(self)
        glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE)
        fbo = self.auxfbo
        with fbo:
            fbo.texture = self.tex
            hp, hp_bg = common_res.hp, common_res.hp_bg

            # hp bar
            glColor3f(1, 1, 1)
            w, h = hp_bg.width * p.maxlife, hp_bg.height
            if w:
                common_res.hp_bg.get_region(0, 0, w, h).blit(5, 55)

            w, h = hp.width * max(p.life, 0), hp.height
            if w:
                common_res.hp.get_region(0, 0, w, h).blit(5, 55)


            glPolygonMode(GL_BACK, GL_LINE)
            w, h = self.width, self.height
            # equip box
            glColor3f(1, 1, 1)
            glRectf(2, 2, w-2, 54)
            glColor3f(*[i/255.0 for i in self.color.heavy])
            glRectf(2.5, 54.5, 2.5+4*36, 2.5)

            # cardnum box
            glColor3f(*[i/255.0 for i in self.color.light])
            glRectf(w-2-32, 66,  w-2, 66+22)
            glColor3f(*[i/255.0 for i in self.color.heavy])
            glRectf(w-2-32, 66+22,  w-2, 66)

            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            # char name
            f = pyglet.font.load('AncientPix', size=9)
            glyphs = f.get_glyphs(meta.char_name)
            gh = f.ascent - f.descent
            glColor3f(1, 1, 1)
            with shaders.FontShadow as fs:
                fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.7)
                glPushMatrix()
                glTranslatef(7, self.height - 30, 0)
                for g in glyphs:
                    glTranslatef(0, -gh, 0)
                    # HACK: pyglet implementation detail
                    # g.vertices = (left_side_bearing, -baseline, ...)
                    g.blit(g.vertices[0], g.vertices[1])
                glPopMatrix()


            gtex = self.grayed_tex
            if not gtex or (gtex.width, gtex.height) != (self.width, self.height):
                self.grayed_tex = gtex = pyglet.image.Texture.create(w, h)

            fbo.texture = gtex
            with shaders.Grayscale:
                self.tex.blit(0, 0)

    def draw(self):
        p = self.player
        if getattr(p, 'dead', False):
            self.tex, tmp = self.grayed_tex, self.tex
            Dialog.draw(self)
            self.tex = tmp
        else:
            Dialog.draw(self)

        w, h = self.width, self.height
        p = self.player
        glColor3f(1, 1, 1)
        try:
            n = len(p.cards) + len(p.showncards)
            seq = str(n)
            ox = (32 - len(seq)*14)//2
            nums = common_res.num
            for i, ch in enumerate(seq):
                n = ord(ch) - ord('0')
                x, y = w - 34 + ox + i*14, 68
                nums[n].blit(w - 34 + ox + i*14, 68)
        except AttributeError as e:
            pass

        if self.disabled:
            glColor4f(0, 0, 0, 0.5)
            glRectf(0, 0, self.width, self.height)
        if self.selected:
            glColor4f(1, 1, 0.8, 0.6)
            glRectf(0, 0, self.width, self.height)

        self.equipcard_area.do_draw()

    @property
    def zindex(self):
        return 0

    @zindex.setter
    def zindex(self, val):
        pass

    def delete(self):
        Dialog.delete(self)
        self.portcard_area.delete()

    def tagarrange(self):
        self._tagarrange_funcs[self.tag_placement]()
