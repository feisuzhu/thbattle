# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Button, TextBox, Control, message as ui_message
from client.ui.controls_extra import *
from client.ui import resource as common_res
import resource as gres
from utils import IRP

from actions import *
from game.autoenv import EventHandler, Action, GameError

card_img = dict(
    attack=gres.card_attack,
    graze=gres.card_graze,
    heal=gres.card_heal,
    hidden=common_res.card_hidden,
)

class UIEventHook(EventHandler):
    def evt_action_after(self, evt):
        ui_message('game_action_after', evt)
        return evt

    def evt_user_input(self, input):
        irp = IRP()
        irp.input = None
        irp.attachment = input.attachment
        ui_message('input_%s' % input.tag, irp)
        irp.wait()
        input.input = irp.input
        return input

    def handle(self, evt, data):
        name = 'evt_%s' % evt
        print name
        if hasattr(self, name):
            return getattr(self, name)(data)
        return data

class SimpleGameUI(Control):
    portrait_location = [ # [ ((x, y), (r, g, b)) ] * Game.n_persons
        ((352, 450), (0, 0, 0)),
        ((200, 150), (0, 0, 0)),
        ((500, 150), (0, 0, 0)),
    ]

    def __init__(self, game, *a, **k):
        self.game = game
        game.event_handlers.append(UIEventHook())
        Control.__init__(self, *a, **k)
        self.btn_ok = Button(
            parent=self, caption=u'确定', x=333, y=202, width=80, height=30
        )
        self.btn_cancel = Button(
            parent=self, caption=u'取消', x=430, y=201, width=80, height=30
        )
        self.prompt = pyglet.text.Label(
            text='youmu youmu youmu', font_size=20, color=(0,0,0,255),
            x=280, y=413, anchor_y = 'bottom'
        )

        self.handcard_area = HandCardArea(
            parent=self, x=238, y=13, zindex=3,
        )

        @self.btn_ok.event
        def on_click():
            irp = self.irp
            irp.input = eval(self.textbox.text)
            irp.complete()
            self._cancel_inputstate()

        @self.btn_cancel.event
        def on_click():
            irp = self.irp
            irp.input = None
            irp.complete()
            self._cancel_inputstate()

    def init(self):
        self.char_portraits = [
            GameCharacterPortrait(parent=self, x=x, y=y)
            for x, y in ((3, 4), (158, 446), (521, 446))
        ]
        self.input_state = False

        shift = self.game.players.index(self.game.me)
        for i, c in enumerate(self.char_portraits):
            c.player_index = (shift + i) % self.game.n_persons

        self.input_players = []

    def _set_inputstate(self):
        self.btn_ok.state = Button.NORMAL
        self.btn_cancel.state = Button.NORMAL
        self.input_state = True

    def _cancel_inputstate(self):
        self.btn_ok.state = Button.DISABLED
        self.btn_cancel.state = Button.DISABLED
        self.input_state = False
        self.input_players = []
        for c in self.char_portraits:
            c.selected = False

    def on_message(self, _type, *args):
        if _type.startswith('input_'):
            self.irp = args[0]
            self._set_inputstate()
            self.prompt.text = _type[6:]
        if _type == 'game_action_after':
            evt = args[0]
            if isinstance(evt, DrawCards) and evt.target is self.game.me:
                cards = evt.cards
                csl = [CardSprite(
                        parent=self, x=410, y=300,
                        img = card_img.get(c.type),
                ) for c in cards]
                self.handcard_area.add_cards(csl)

    def on_mouse_click(self, x, y, button, modifier):
        if self.input_state:
            c = self.control_frompoint1(x, y)
            if isinstance(c, GameCharacterPortrait):
                sel = not c.selected
                c.selected = sel
                if sel:
                    self.input_players.append(c.player_index)
                else:
                    self.input_players.remove(c.player_index)

    def draw(self, dt):
        self.prompt.draw()
        self.draw_subcontrols(dt)
