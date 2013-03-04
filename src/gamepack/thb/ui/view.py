# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control, ui_message, Overlay, process_msg
from client.ui.controls import *
from client.ui import resource as common_res
from client.ui import shaders, soundmgr
import resource as gres
from utils import IRP, hook

from .game_controls import *

from game.autoenv import EventHandler, Action, GameError

import logging
log = logging.getLogger('THBattleUI')

import effects, inputs

from .. import actions

class UIEventHook(EventHandler):
    @classmethod
    def evt_user_input(cls, input):
        irp = IRP()
        irp.__dict__.update(input.__dict__)
        ui_message('evt_user_input', irp)
        irp.wait()
        input.input = irp.input
        return input

    @classmethod
    def evt_shuffle_cards(cls, args):
        cls.ui_barrier_schedule(lambda: None)
        return args

    @classmethod
    def evt_action_after(cls, act):
        if hasattr(act, 'ui_meta'):
            if getattr(act.ui_meta, 'barrier', False):
                cls.ui_barrier_schedule(process_msg, ('evt_action_after', act))
                return act

        ui_message('evt_action_after', act)
        return act

    @classmethod
    def ui_barrier_schedule(cls, cb, *args, **kwargs):
        irp = IRP()

        def ui_callback():
            cb(*args, **kwargs)
            irp.complete()

        ui_schedule(ui_callback)
        import gevent
        gevent.sleep(0.02)
        irp.wait()

    # evt_user_input_timeout, InputControllers handle this

    @classmethod
    def handle(cls, evt, data):
        name = 'evt_%s' % evt
        try:
            f = getattr(cls, name)
        except AttributeError:
            ui_message(name, data)
            return data

        rst = f(data)
        return rst


class DeckIndicator(Control):
    def draw(self):
        w, h = self.width, self.height
        g = Game.getgame()
        try:
            n = len(g.deck.cards)
        except AttributeError:
            return

        glColor3f(*[i/255.0 for i in Colors.blue.light])
        glRectf(0, 0,  w, h)
        glColor3f(*[i/255.0 for i in Colors.blue.heavy])
        glRectf(0, h, w, 0)

        glColor3f(1, 1, 1)
        try:
            nums = gres.num
            seq = str(n)
            ox = (w - len(seq)*14)//2
            oy = (h - nums[0].height)//2
            with nums[0].owner:
                for i, ch in enumerate(seq):
                    n = ord(ch) - ord('0')
                    #x, y = w - 34 + ox + i*14, 68
                    nums[n].blit_nobind(ox + i*14, oy)
        except AttributeError as e:
            pass

class ResultPanel(Panel):
    fill_color = (1.0, 1.0, 0.9, 0.5)
    def __init__(self, g, *a, **k):
        Panel.__init__(self, width=550, height=340, zindex=10000, *a, **k)
        parent = self.parent
        self.x = (parent.width - 550) // 2
        self.y = (parent.height - 340) // 2
        self.textarea = ta = TextArea(
            parent=self, x=30, y=30, width=550-30, height=340-60,
            font_size=12,
        )
        ta.text = u''
        winners = g.winners
        for p in g.players:
            s = u'|G%s|r(|R%s|r, |c0000ffff%s|r, %s)\n' % (
                p.ui_meta.char_name, p.account.username.replace('|', '||'),
                g.ui_meta.identity_table[p.identity.type],
                u'|R胜利|r' if p in winners else u'失败'
            )
            ta.append(s)

        if g.me in winners:
            self.pic = gres.win
        else:
            self.pic = gres.lose

        close = Button(
            u'关闭', parent=self, x=440, y=25, width=90, height=40
        )

        @close.event
        def on_click():
            self.delete()

    def draw(self):
        Panel.draw(self)
        pic = self.pic
        glColor3f(1, 1, 1)
        self.pic.blit(self.width - pic.width - 10, self.height - pic.height - 10)


class THBattleUI(Control):
    portrait_location = [
        (60, 300, Colors.blue),
        (250, 450, Colors.orange),
        (450, 450, Colors.blue),
        (640, 300, Colors.orange),
        (450, 150, Colors.blue),
        (250, 150, Colors.orange),
    ]

    gcp_location = [
        (3, 1, 'me', Colors.blue),
        (669, 280, 'left', Colors.orange),
        (155+180+180, 520, 'bottom', Colors.blue),
        (155+180, 520, 'bottom', Colors.orange),
        (155, 520, 'bottom', Colors.blue),
        (3, 280, 'right', Colors.orange),
    ]

    def __init__(self, game, *a, **k):
        self.game = game
        game.event_observer = UIEventHook

        Control.__init__(self, *a, **k)

        self.char_portraits = None

        self.deck_indicator = DeckIndicator(
            parent=self, x=30, y=680, width=50, height=25,
        )

        self.handcard_area = HandCardArea(
            parent=self, x=238, y=9, zindex=3,
            width=93*5+42, height=145,
        )

        self.deck_area = PortraitCardArea(
            parent=self, width=1, height=1,
            x=self.width//2, y=self.height//2, zindex=4,
        )

        self.btn_afk = Button(
            parent=self, caption=u'让⑨帮你玩', zindex=1,
            color=Colors.blue,
            **r2d((730, 640, 75, 25))
        )

        self.afk = False

        @self.btn_afk.event
        def on_click():
            v = not self.afk
            self.afk = v
            self.btn_afk.color = (Colors.blue, Colors.orange)[v]
            self.btn_afk.update()

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
            GameCharacterPortrait(parent=self, color=color, x=x, y=y, tag_placement=tp)
            for x, y, tp, color in self.gcp_location[:len(self.game.players)]
        ]

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

        soundmgr.switch_bgm(gres.bgm_game)

    def player2portrait(self, p):
        for port in self.char_portraits:
            if port.player == p:
                break
        else:
            raise ValueError(p)
        return port

    def update_skillbox(self):
        g = self.game
        skills = getattr(g.me, 'skills', None)
        if skills is None:
            # before girl chosen
            return

        skills = [
            (i, s, s.ui_meta.clickable(g))
            for i, s in enumerate(skills)
            if not getattr(s.ui_meta, 'no_display', False)
        ]

        skills.sort(key=lambda i: -i[2])

        self.skill_box.set_skills(
            (s.ui_meta.name, i, e) for i, s, e in skills
        )

    PORT_UPDATE_MESSAGES = {
        'evt_game_begin',
        'evt_girl_chosen',
        'evt_girl_chosen_end',
        'evt_kof_next_character',
    }

    def on_message(self, _type, *args):
        if _type == 'evt_action_before' and isinstance(args[0], actions.PlayerTurn):
            self.current_turn = args[0].target

        elif _type == 'player_change':
            for i, pd in enumerate(args[0]):
                p = self.game.players[i]
                port = self.player2portrait(p)
                port.dropped = (pd['state'] in { 'dropped', 'fleed' })
                port.fleed = (pd['state'] == 'fleed')
                port.update()

        elif _type in self.PORT_UPDATE_MESSAGES:
            for port in self.char_portraits:
                port.update()

        elif _type == 'evt_action_after':
            act = args[0]
            meta = getattr(act, 'ui_meta', None)
            if meta and getattr(meta, 'update_portrait', None):
                pl = set()
                if act.source:
                    pl.add(act.source)

                if hasattr(act, 'target_list'):
                    pl.update(act.target_list)
                elif act.target:
                    pl.add(act.target)

                for p in pl:
                    self.player2portrait(p).update()

        if _type.startswith('evt_'):
            effects.handle_event(self, _type[4:], args[0])
            inputs.handle_event(self, _type[4:], args[0])

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
        for p in self.game.players:
            port = self.player2portrait(p)

            if p in disables:
                port.disabled = True
                port.selected = False
                try:
                    self.selected_players.remove(p)
                except ValueError:
                    pass
            else:
                port.disabled = False

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
        c = self.control_frompoint1_recursive(x, y)
        if isinstance(c, GameCharacterPortrait) and self.selecting_player and not c.disabled:
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

    def get_game_screen(self):
        assert self.parent
        return self.parent

    @staticmethod
    def show_result(g):
        ResultPanel(g, parent=Overlay.cur_overlay)


THBattleUI.register_event_type('on_selection_change')


class THBattleIdentityUI(THBattleUI):
    portrait_location = [
        (150, 430, Colors.blue),
        (290, 430, Colors.blue),
        (430, 430, Colors.blue),
        (570, 430, Colors.blue),

        (150, 170, Colors.blue),
        (290, 170, Colors.blue),
        (430, 170, Colors.blue),
        (570, 170, Colors.blue),
    ]

    gcp_location = [
        (3, 1, 'me', Colors.blue),
        (669, 210, 'left', Colors.blue),
        (669, 420, 'left', Colors.blue),
        (505, 520, 'bottom', Colors.blue),
        (335, 520, 'bottom', Colors.blue),
        (165, 520, 'bottom', Colors.blue),
        (3, 420, 'right', Colors.blue),
        (3, 210, 'right', Colors.blue),
    ]


class THBattleIdentity5UI(THBattleIdentityUI):
    portrait_location = [
        (290, 450, Colors.blue),
        (490, 450, Colors.blue),

        (190, 150, Colors.blue),
        (380, 150, Colors.blue),
        (570, 150, Colors.blue),
    ]

    gcp_location = [
        (3, 1, 'me', Colors.blue),
        (669, 270, 'left', Colors.blue),
        (455, 520, 'bottom', Colors.blue),
        (215, 520, 'bottom', Colors.blue),
        (3, 270, 'right', Colors.blue),
    ]


class THBattleKOFUI(THBattleUI):
    portrait_location = [
        (250, 300, Colors.orange),
        (450, 300, Colors.blue),
    ]

    gcp_location = [
        (3, 1, 'me', Colors.blue),
        (335, 520, 'bottom', Colors.orange),
    ]


class THBattleRaidUI(THBattleUI):
    portrait_location = [
        (290, 450, Colors.red),
        (490, 450, Colors.blue),
        (190, 150, Colors.blue),
        (380, 150, Colors.blue),
    ]

    gcp_location = [
        (3, 1, 'me', Colors.blue),
        (669, 270, 'left', Colors.blue),
        (455, 520, 'bottom', Colors.blue),
        (215, 520, 'bottom', Colors.blue),
    ]
