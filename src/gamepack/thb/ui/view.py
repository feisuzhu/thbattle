# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control, message as ui_message
from client.ui.controls import *
from client.ui import resource as common_res
from client.ui import shaders
import resource as gres
from utils import IRP

from game.autoenv import EventHandler, Action, GameError

import logging
log = logging.getLogger('THBattleUI')

import effects, inputs

class UIEventHook(EventHandler):

    def evt_user_input(self, input):
        irp = IRP()
        irp.__dict__.update(input.__dict__)
        ui_message('evt_user_input', irp)
        irp.wait()
        input.input = irp.input
        return input

    # evt_user_input_timeout, InputControllers handle this

    def handle(self, evt, data):
        name = 'evt_%s' % evt
        try:
            f = getattr(self, name)
        except AttributeError:
            ui_message(name, data)
            return data

        return f(data)

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

class SmallCardSprite(Control):
    width, height = 33, 46
    x = InterpDesc('_x')
    y = InterpDesc('_y')
    def __init__(self, img, x=0.0, y=0.0, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 33, 46
        self.x, self.y = x, y
        self.selected = False
        self.hover = False
        self.img = img

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
        for c in player.shown_cards:
            cs = CardSprite(
                parent=ca,
                img=c.ui_meta.image,
                number=c.number,
                suit=c.suit,
            )
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
        with self.fbo:
            with shaders.FontShadow as fs:
                fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.9)
                self.lbl.draw()

    def delete(self):
        Panel.delete(self)
        ShownCardPanel.current = None

class GameCharacterPortrait(Dialog):

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
            if not hasattr(p, 'shown_cards'): return # before the 'real' game start
            last = ShownCardPanel.current
            if last:
                last.delete()
                if last.player is p:
                    return
            ShownCardPanel(p, parent=self.parent)

    def update(self):
        p = self.player
        if not p: return


        self.caption = p.nickname
        try:
            meta = p.ui_meta

        except AttributeError:
            # before girls chosen
            Dialog.update(self)
            return

        self.bg = meta.port_image

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

            w, h = hp.width * p.life, hp.height
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

    def draw(self):
        Dialog.draw(self)
        w, h = self.width, self.height
        p = self.player
        glColor3f(1, 1, 1)
        try:
            n = len(p.cards) + len(p.shown_cards)
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

class THBattleUI(Control):
    portrait_location = [ # [ ((x, y), (r, g, b)) ] * Game.n_persons
        # XXX: color n/a any more
        ((352, 450), (0, 0, 0)),
        ((200, 150), (0, 0, 0)),
        ((500, 150), (0, 0, 0)),
    ]

    def __init__(self, game, *a, **k):
        self.game = game
        self.hook = hook = UIEventHook()
        game.event_handlers.append(hook)
        Control.__init__(self, *a, **k)

        self.handcard_area = HandCardArea(
            parent=self, x=238, y=9, zindex=3,
            width=93*5+42, height=145,
        )

        self.deck_area = PortraitCardArea(
            parent=self, width=1, height=1,
            x=self.width//2, y=self.height//2, zindex=4,
        )


        @self.handcard_area.event
        def on_selection_change():
            self.dispatch_event('on_selection_change')

        self.dropcard_area = DropCardArea(
            parent=self, x=0, y=324, zindex=3,
            width=820, height=125,
        )

        class Animations(pyglet.graphics.Batch, Control):
            def __init__(self, **k):
                pyglet.graphics.Batch.__init__(self)
                Control.__init__(
                    self, x=0, y=0,
                    width=0, height=0, zindex=2,
                    **k
                )

            def hit_test(self, x, y):
                return False

        self.animations = Animations(parent=self)
        self.selecting_player = 0


    def init(self):
        ports = self.char_portraits = [
            GameCharacterPortrait(parent=self, x=x, y=y, tag_placement=tp)
            for x, y, tp in ((3, 1, 'me'), (158, 446, 'bottom'), (521, 446, 'bottom'))[:len(self.game.players)]
        ] # FIXME: this is for testing

        pl = self.game.players
        shift = pl.index(self.game.me)
        for i, c in enumerate(ports):
            p = pl[(shift + i) % self.game.n_persons]
            c.player = p
            c.update()

        ports[0].equipcard_area.selectable = True # it's TheChosenOne

        self.begin_select_player()
        self.end_select_player()
        self.skill_box = SkillSelectionBox(
            parent=self, x=161, y=9, width=70, height=22*6-4
        )

    def player2portrait(self, p):
        for port in self.char_portraits:
            if port.player == p:
                break
        else:
            raise ValueError
        return port

    def update_skillbox(self):
        g = self.game
        skills = getattr(g.me, 'skills', None)
        if skills is None:
            # before girl chosen
            return
        skills = [(i, s) for i, s in enumerate(skills) if not getattr(s.ui_meta, 'no_display', False)]
        self.skill_box.set_skills(
            (s.ui_meta.name, i) for i, s in skills
        )

        for sb, (_, skill) in zip(self.skill_box.buttons, skills):
            if skill.ui_meta.clickable(g):
                sb.state = Button.NORMAL

    def on_message(self, _type, *args):
        if _type == 'evt_game_begin':
            for port in self.char_portraits:
                port.update()
            self.update_skillbox()
            '''
            # HACK: move UIEventHook to the end of EH list

            ehlist = self.game.event_handlers
            hook = self.hook
            ehlist.remove(hook)
            ehlist.append(hook)

            for i in ehlist:
                print i.__class__
            '''

        elif _type == 'evt_player_turn':
            self.current_turn = args[0]

        if _type.startswith('evt_'):
            inputs.handle_event(self, _type[4:], args[0])
            effects.handle_event(self, _type[4:], args[0])

    def draw(self):
        self.draw_subcontrols()

    def ray(self, f, t):
        if f == t: return
        sp = self.player2portrait(f)
        dp = self.player2portrait(t)
        x0, y0 = sp.x + sp.width/2, sp.y + sp.height/2
        x1, y1 = dp.x + dp.width/2, dp.y + dp.height/2
        Ray(x0, y0, x1, y1, parent=self, zindex=10)

    def prompt(self, s):
        self.prompt_raw(u'|B|cff0000ff>> |r' + unicode(s) + u'\n')

    def prompt_raw(self, s):
        self.parent.events_box.append(s)

    def begin_select_player(self, disables=[]):
        #if self.selecting_player: return
        self.selecting_player = True
        #self.selected_players = []
        for p in disables:
            self.player2portrait(p).disabled = True

    def get_selected_players(self):
        return self.selected_players

    def set_selected_players(self, players):
        for p in self.char_portraits:
            p.selected = False

        for p in players:
            self.player2portrait(p).selected = True

        self.selected_players = players[:]

    def end_select_player(self):
        #if not self.selecting_player: return
        self.selecting_player = False
        self.selected_players = []
        for p in self.char_portraits:
            p.selected = False
            p.disabled = False

    def get_selected_cards(self):
        return [
            cs.associated_card
            for cs in self.handcard_area.cards
            if cs.hca_selected
        ] + [
            cs.associated_card
            for cs in self.player2portrait(self.game.me).equipcard_area.cards
            if cs.selected
        ]

    def get_selected_skills(self):
        skills = self.game.me.skills
        return sorted([
            skills[i] for i in self.skill_box.get_selected_index()
        ], key=lambda s: s.sort_index)

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        if isinstance(c, GameCharacterPortrait) and (
            self.selecting_player) and (not c.disabled) and (
            not c.control_frompoint1(x-c.x, y-c.y)):

            sel = c.selected
            psel = self.selected_players
            if sel:
                c.selected = False
                psel.remove(c.player)
            else:
                c.selected = True
                psel.append(c.player)
            self.dispatch_event('on_selection_change')
        return True

THBattleUI.register_event_type('on_selection_change')
