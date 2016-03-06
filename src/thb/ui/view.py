# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --
from pyglet.gl import glColor3f, glRectf
import pyglet

# -- own --
from client.ui.base import Control, Overlay
from client.ui.controls import BalloonPrompt, Button, Colors, OptionButton, Panel, TextArea
from client.ui.resloader import L
from client.ui.soundmgr import SoundManager
from game.autoenv import Game
from thb import actions
from thb.ui import effects, inputs
from thb.ui.game_controls import CardSprite, DropCardArea, GameCharacterPortrait
from thb.ui.game_controls import HandCardArea, PortraitCardArea, Ray, SkillSelectionBox
from utils import rect_to_dict as r2d
from utils.misc import ObservableEvent


# -- code --
log = logging.getLogger('THBattleUI')


class DeckIndicator(Control):
    def draw(self):
        w, h = self.width, self.height
        g = Game.getgame()
        try:
            n = len(g.deck.cards)
        except AttributeError:
            return

        glColor3f(*[i/255.0 for i in Colors.blue.light])
        glRectf(0, 0, w, h)
        glColor3f(*[i/255.0 for i in Colors.blue.heavy])
        glRectf(0, h, w, 0)

        glColor3f(1, 1, 1)
        try:
            nums = L('thb-num')
            seq = str(n)
            ox = (w - len(seq)*14) // 2
            oy = (h - nums[0].height) // 2
            with nums[0].owner:
                for i, ch in enumerate(seq):
                    n = ord(ch) - ord('0')
                    # x, y = w - 34 + ox + i*14, 68
                    nums[n].blit_nobind(ox + i*14, oy)

        except AttributeError:
            pass


class ResultPanel(Panel):
    fill_color = (1.0, 1.0, 0.9, 0.5)

    def __init__(self, g, *a, **k):
        Panel.__init__(self, width=550, height=340, zindex=15, *a, **k)
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
            self.pic = L('thb-win')
        else:
            self.pic = L('thb-lose')

        close = Button(
            u'关闭', parent=self, x=440, y=25, width=90, height=40, zindex=10,
        )

        @close.event
        def on_click():
            self.delete()

    def draw(self):
        Panel.draw(self)
        pic = self.pic
        glColor3f(1, 1, 1)
        self.pic.blit(self.width - pic.width - 10, self.height - pic.height - 10)


class GameIntroIcon(Control):
    def __init__(self, game, *a, **k):
        Control.__init__(self, *a, **k)
        intro = getattr(game.ui_meta, 'description', None)
        if intro:
            balloon = BalloonPrompt(self)
            balloon.set_balloon(intro, width=480)

    def draw(self):
        glColor3f(1, 1, 1)
        L('thb-tag-gameintro').blit(0, 0)


class THBattleUI(Control):
    portrait_location = [
        (60,  290, Colors.blue),
        (250, 440, Colors.orange),
        (450, 440, Colors.blue),
        (640, 290, Colors.orange),
        (450, 140, Colors.blue),
        (250, 140, Colors.orange),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (669, 280, 'left',   Colors.orange),
        (515, 500, 'bottom', Colors.blue),
        (335, 500, 'bottom', Colors.orange),
        (155, 500, 'bottom', Colors.blue),
        (3,   280, 'right',  Colors.orange),
    ]

    def __init__(self, game, *a, **k):
        self.selection_change = ObservableEvent()

        self.game = game

        Control.__init__(self, can_focus=True, *a, **k)

        self.keystrokes = '\x00'
        self.char_portraits = None

        self.deck_indicator = DeckIndicator(
            parent=self, x=30, y=660, width=50, height=25,
        )

        self.handcard_area = HandCardArea(
            parent=self, view=self, x=238, y=9, zindex=3,
            width=93*5+42, height=145,
        )

        self.deck_area = PortraitCardArea(
            parent=self, width=1, height=1,
            x=self.width//2, y=self.height//2, zindex=4,
        )

        self.btn_afk = OptionButton(
            parent=self, zindex=1, conf=(
                (u'让⑨帮你玩', Colors.blue, False),
                (u'⑨在帮你玩', Colors.orange, True),
            ), **r2d((30, 625, 75, 25))
        )

        self.gameintro_icon = GameIntroIcon(
            parent=self, game=game,
            **r2d((690, 630, 25, 25))
        )

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
                self.animations = []

            def delete(self):
                Control.delete(self)
                for a in self.animations:
                    a.delete()

            def hit_test(self, x, y):
                return False

        self.animations = Animations(parent=self)
        self.selecting_player = 0
        self.action_params = {}

    @property
    def afk(self):
        return self.btn_afk.value

    def init(self):
        SoundManager.se_suppress()
        self.game_event = ObservableEvent()
        self.process_game_event = self.game_event.notify

        self.game_event += self.on_game_event

        n = len(self.game.players)
        ports = self.char_portraits = [
            GameCharacterPortrait(parent=self, color=color,
                                  x=x, y=y, tag_placement=tp)
            for x, y, tp, color in self.gcp_location[:n]
        ]

        pl = self.game.players
        shift = pl.index(self.game.me)
        for i, c in enumerate(ports):
            self.game_event += c.on_game_event
            p = pl[(shift + i) % n]
            c.player = p
            c.update()

        ports[0].equipcard_area.selectable = True  # it's TheChosenOne

        self.begin_select_player()
        self.end_select_player()
        self.skill_box = SkillSelectionBox(
            parent=self, x=161, y=9, width=70, height=22*6-4
        )

        SoundManager.switch_bgm('thb-bgm_game')

        self.more_init()

    def more_init(self):
        pass

    def set_live(self):
        SoundManager.se_unsuppress()
        self.update_portraits_hard()
        self.update_handcard_area()
        self.refresh_input_state()

    def player2portrait(self, p):
        from thb.characters.baseclasses import Character
        if isinstance(p, Character):
            p = p.player

        for port in self.char_portraits:
            if port.player == p:
                break
        else:
            raise ValueError(p)
        return port

    def refresh_input_state(self):
        self.action_params = {}

        g = self.game
        skills = getattr(g.me, 'skills', None)
        if skills is not None:
            skills = [
                (s, i, s.ui_meta.clickable(g))
                for i, s in enumerate(skills)
                if not getattr(s.ui_meta, 'no_display', False)
            ]

            skills.sort(key=lambda i: -i[2])

            self.skill_box.set_skills(skills)

    def update_portraits(self):
        for port in self.char_portraits:
            port.update()

    def update_portraits_hard(self):
        g = self.game
        for p in g.players:
            port = self.player2portrait(p)
            port.update_identity(p)
            port.clear_equip_sprites()
            if not hasattr(p, 'equips'): continue
            port.add_equip_sprites(p.equips)
            effects.update_tags(self, p)
            port.update()

    def update_handcard_area(self):
        g = self.game
        me = g.me
        if not hasattr(me, 'cards'): return

        hca = self.handcard_area

        for c in hca.cards[:]:
            c.delete()

        for c in list(me.cards) + list(me.showncards):
            cs = CardSprite(c, parent=hca)
            cs.associated_card = c

        hca.update()

    def on_message(self, _type, *args):
        if _type == 'player_change':
            for i, pd in enumerate(args[0]):
                p = self.game.players[i]
                port = self.player2portrait(p)
                port.dropped = (pd['state'] in ('dropped', 'fleed'))
                port.fleed = (pd['state'] == 'fleed')
                port.update()

    def on_game_event(self, evt_type, arg):
        if evt_type == 'action_before' and isinstance(arg, actions.PlayerTurn):
            self.current_player = arg.target

        elif evt_type in ('game_begin', 'switch_character'):
            self.update_portraits()

        elif evt_type == 'action_after':
            act = arg
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

        effects.handle_event(self, evt_type, arg)
        inputs.handle_event(self, evt_type, arg)

    def more_on_message(self, _type, args):
        pass

    def on_text(self, text):
        # The easter egg
        ks = self.keystrokes
        ks = (ks + text)[:40]
        self.keystrokes = ks

        from thb.characters.baseclasses import Character

        for c in Character.character_classes.itervalues():
            try:
                alter = c.ui_meta.figure_image_alter
            except:
                continue

            for i in xrange(len(ks)):
                if L(alter).decrypt(ks[-i:]):
                    SoundManager.play('c-sound-input')

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
        self.parent and self.parent.events_box.append(s)

    def begin_select_player(self, disables=[]):
        # if self.selecting_player: return
        self.selecting_player = True
        # self.selected_players = []
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
        # if not self.selecting_player: return
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

    def reset_selected_skills(self):
        self.skill_box.reset()

    def get_action_params(self):
        return self.action_params

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1_recursive(x, y)
        if isinstance(c, GameCharacterPortrait) and self.selecting_player and not c.disabled:
            char = c.character
            if not char: return True
            sel = c.selected
            psel = self.selected_players
            if sel:
                c.selected = False
                psel.remove(char)
            else:
                c.selected = True
                psel.append(char)

            self.selection_change.notify()
        return True

    def get_game_screen(self):
        assert self.parent
        return self.parent

    @staticmethod
    def show_result(g):
        ResultPanel(g, parent=Overlay.cur_overlay)


class THBattleIdentityUI(THBattleUI):
    portrait_location = [
        (150, 420, Colors.blue),
        (290, 420, Colors.blue),
        (430, 420, Colors.blue),
        (570, 420, Colors.blue),

        (150, 160, Colors.blue),
        (290, 160, Colors.blue),
        (430, 160, Colors.blue),
        (570, 160, Colors.blue),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (669, 210, 'left',   Colors.blue),
        (669, 420, 'left',   Colors.blue),
        (505, 500, 'bottom', Colors.blue),
        (335, 500, 'bottom', Colors.blue),
        (165, 500, 'bottom', Colors.blue),
        (3,   420, 'right',  Colors.blue),
        (3,   210, 'right',  Colors.blue),
    ]


class THBattleKOFUI(THBattleUI):
    portrait_location = [
        (250, 290, Colors.orange),
        (450, 290, Colors.blue),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (335, 500, 'bottom', Colors.orange),
    ]


class THBattleFaithUI(THBattleUI):
    portrait_location = [
        (60,  290, Colors.blue),
        (250, 440, Colors.orange),
        (450, 440, Colors.blue),
        (640, 290, Colors.orange),
        (450, 140, Colors.blue),
        (250, 140, Colors.orange),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (669, 280, 'left',   Colors.blue),
        (515, 500, 'bottom', Colors.blue),
        (335, 500, 'bottom', Colors.blue),
        (155, 500, 'bottom', Colors.blue),
        (3,   280, 'right',  Colors.blue),
    ]

    def more_init(self):
        self.remaining_indicator = TextArea(
            parent=self, x=25, y=560, width=100, height=50, font_size=12,
        )
        self.game_event += self.handle_remaining_indicator

    def handle_remaining_indicator(self, evt_type, arg):
        if evt_type in ('switch_character', 'action_stage_action'):
            h, m = self.game.get_remaining_characters()
            if h < 0 or m < 0:
                return

            self.remaining_indicator.text = (
                u'|s1e5effbff|c315597ff博丽：%d 人|r\n'
                u'|s1886666ff|W守矢：%d 人|r'
            ) % (h, m)


class THBattle2v2UI(THBattleUI):
    portrait_location = [
        (250, 440, Colors.blue),
        (450, 440, Colors.blue),
        (450, 140, Colors.orange),
        (250, 140, Colors.orange),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (669, 270, 'left',   Colors.blue),
        (335, 500, 'bottom', Colors.blue),
        (3,   270, 'right',  Colors.blue),
    ]


class THBattleBookUI(THBattleUI):
    portrait_location = [
        (250, 440, Colors.orange),
        (450, 440, Colors.orange),
        (450, 140, Colors.blue),
        (250, 140, Colors.blue),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (669, 270, 'left',   Colors.blue),
        (455, 500, 'bottom', Colors.blue),
        (215, 500, 'bottom', Colors.blue),
        (3,   270, 'right',  Colors.blue),
    ]


class THBattleNewbieUI(THBattleUI):
    portrait_location = [
        (380, 290, Colors.blue),
    ]

    gcp_location = [
        (3,   1,   'me',     Colors.blue),
        (335, 500, 'bottom', Colors.orange),
    ]
