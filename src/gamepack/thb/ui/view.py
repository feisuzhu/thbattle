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

from gamepack.simple.actions import *
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
        def __init__(self, *a, **k):
            Button.__init__(self, width=69, height=20, *a, **k)
            self.selected = False
            self.state = Button.DISABLED
            self.color = Colors.blue
            self.update()

        def on_click(self):
            buttons = self.parent.buttons
            if self.selected:
                self.parent.selection.remove(buttons.index(self))
                self.color = Colors.blue
                self.selected = False
                self.update()
            else:
                self.color = Colors.orange
                self.update()
                self.parent.selection.append(buttons.index(self))
                self.selected = True

            self.parent.parent.dispatch_event('on_selection_change')

    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.selection = []

    def set_skills(self, lst):
        # lst = ('name1', 'name2', ...)
        y = self.height
        for b in self.buttons[:]:
            b.delete()

        assert not self.buttons

        for n in lst:
            y -= 22
            SkillSelectionBox.SkillButton(n, parent=self, x=0, y=y)

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

class GameCharacterPortrait(Dialog):
    def __init__(self, color=Colors.blue, *args, **kwargs):
        self.selected = False
        self.maxlife = 8
        self.life = 0
        self.name = u''
        self.char_name = u''
        Dialog.__init__(
            self, width=149, height=195,
            bot_reserve=74, color=color,
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

    def update(self):
        self.caption = self.name

        try:
            self.bg = self.port_image
        except AttributeError:
            pass

        Dialog.update(self)
        with self.fbo:
            hp, hp_bg = common_res.hp, common_res.hp_bg

            # hp bar
            glColor3f(1, 1, 1)
            w, h = hp_bg.width * self.maxlife, hp_bg.height
            if w:
                common_res.hp_bg.get_region(0, 0, w, h).blit(5, 55)

            w, h = hp.width * self.life, hp.height
            if w:
                common_res.hp.get_region(0, 0, w, h).blit(5, 55)

            # equip boxes
            glColor3f(1, 1, 1)
            glRectf(2, 2, self.width-2, 54)
            glLineWidth(2.0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3f(*[i/255.0 for i in self.color.heavy])
            pyglet.graphics.draw(
                10, GL_QUAD_STRIP, ('v2f', (
                    2 + 0*36, 3,   2 + 0*36, 54,
                    2 + 1*36, 3,   2 + 1*36, 54,
                    2 + 2*36, 3,   2 + 2*36, 54,
                    2 + 3*36, 3,   2 + 3*36, 54,
                    2 + 4*36, 3,   2 + 4*36, 54,
                ))
            )
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glLineWidth(1.0)

            # char name
            f = pyglet.font.load('AncientPix', size=9)
            glyphs = f.get_glyphs(self.char_name)
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
        if self.disabled:
            glColor4f(0, 0, 0, 0.5)
            glRectf(0, 0, self.width, self.height)
        if self.selected:
            glColor4f(1, 1, 0.8, 0.6)
            glRectf(0, 0, self.width, self.height)

    @property
    def zindex(self):
        return 0

    @zindex.setter
    def zindex(self, val):
        pass

class THBattleUI(Control):
    portrait_location = [ # [ ((x, y), (r, g, b)) ] * Game.n_persons
        # XXX: color n/a any more
        ((352, 450), (0, 0, 0)),
        ((200, 150), (0, 0, 0)),
        ((500, 150), (0, 0, 0)),
    ]

    def __init__(self, game, *a, **k):
        self.game = game
        game.event_handlers.append(UIEventHook())
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
        self.char_portraits = [
            GameCharacterPortrait(parent=self, x=x, y=y)
            for x, y in ((3, 1), (158, 446), (521, 446))[:len(self.game.players)]
        ] # FIXME: this is for testing

        pl = self.game.players
        shift = pl.index(self.game.me)
        for i, c in enumerate(self.char_portraits):
            p = pl[(shift + i) % self.game.n_persons]
            c.player = p
            c.name = p.nickname
            c.update()

        self.begin_select_player(1)
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
        if not skills:
            # before girl chosen
            return
        skills = [s for s in skills if not getattr(s.ui_meta, 'no_display', False)]
        self.skill_box.set_skills(
            s.ui_meta.name for s in skills
        )

        for sb, skill in zip(self.skill_box.buttons, skills):
            if skill.ui_meta.clickable(g):
                sb.state = Button.NORMAL

    def on_message(self, _type, *args):
        if _type == 'evt_user_input':
            irp = args[0]
            itype = irp.tag
            cls = inputs.mapping.get(itype)
            if cls:
                self.update_skillbox()
                cls(irp, parent=self)
            else:
                log.error('No apropriate input handler!')
                irp.input = None
                irp.complete()
        elif _type == 'evt_user_input_all_begin':
            arg = args[0]
            itype = arg[0]
            cls = inputs.mapping_all.get(itype)
            if cls:
                cls(attachment=arg[1], parent=self)
        elif _type == 'evt_simplegame_begin':
            for port in self.char_portraits:
                p = port.player
                port.life = p.life
                port.maxlife = p.maxlife
                meta = p.ui_meta
                port.port_image = meta.port_image
                port.char_name = meta.char_name
                port.update()
            self.update_skillbox()

        elif _type == 'evt_player_turn':
            self.current_turn = args[0]

        if _type.startswith('evt_'):
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

    def begin_select_player(self, num, disables=[]):
        if self.selecting_player: return
        self.selecting_player = num
        self.selected_players = []
        for p in disables:
            self.player2portrait(p).disabled = True

    def get_selected_players(self):
        return self.selected_players

    def end_select_player(self):
        if not self.selecting_player: return
        self.selecting_player = 0
        self.selected_players = []
        for p in self.char_portraits:
            p.selected = False
            p.disabled = False

    def get_selected_cards(self):
        return [
            cs.associated_card
            for cs in self.handcard_area.cards
            if cs.hca_selected
        ]

    def get_selected_skills(self):
        skills = self.game.me.skills
        return sorted([
            skills[i] for i in self.skill_box.get_selected_index()
        ], key=lambda s: s.sort_index)

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        if isinstance(c, GameCharacterPortrait) and self.selecting_player and not c.disabled:
            sel = c.selected
            psel = self.selected_players
            nplayers = self.selecting_player
            if sel:
                c.selected = False
                psel.remove(c.player)
            else:
                if nplayers == 1:
                    for port in self.char_portraits:
                        port.selected = False
                    c.selected = True
                    psel = self.selected_players = [c.player]
                elif len(psel) < nplayers:
                    c.selected = True
                    psel.append(c.player)
                # else: do nothing
            self.dispatch_event('on_selection_change')
        return True

THBattleUI.register_event_type('on_selection_change')
