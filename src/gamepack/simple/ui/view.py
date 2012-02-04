# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import message as ui_message
from client.ui.controls import *
from client.ui import resource as common_res
import resource as gres
from utils import IRP

from gamepack.simple.actions import *
from game.autoenv import EventHandler, Action, GameError

import logging
log = logging.getLogger('SimpleGameUI')

class UIEventHook(EventHandler):
    def evt_action_apply(self, evt):
        ui_message('game_action_apply', evt)
        return evt

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

    def evt_user_input_timeout(self, input):
        ui_message('io_timeout', input.tag)

    def evt_simplegame_begin(self, _):
        ui_message('simplegame_begin')

    def handle(self, evt, data):
        name = 'evt_%s' % evt
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

        self.prompt = pyglet.text.Label(
            text='youmu youmu youmu', font_size=20, color=(0,0,0,255),
            x=280, y=413, anchor_y = 'bottom'
        )

        self.handcard_area = HandCardArea(
            parent=self, x=238, y=13, zindex=3,
        )

        self.dropcard_area = DropCardArea(
            parent=self, x=0, y=324, zindex=3,
        )

    def init(self):
        self.char_portraits = [
            GameCharacterPortrait(parent=self, x=x, y=y)
            for x, y in ((3, 4), (158, 446), (521, 446))
        ][:len(self.game.players)] # FIXME: this is for testing
        self.input_state = False

        shift = self.game.players.index(self.game.me)
        for i, c in enumerate(self.char_portraits):
            c.player_index = (shift + i) % self.game.n_persons

        self.player_shift = shift

    def player2portrait(self, c):
        i = self.game.players.index(c)
        p = self.char_portraits[(i - self.player_shift) % self.game.n_persons]
        assert p.player_index == i
        return p

    def on_message(self, _type, *args):
        if _type.startswith('input_'):
            import inputs
            irp = args[0]
            itype = _type[6:]
            self.prompt.text = itype
            cls = inputs.mapping.get(itype)
            if cls:
                cls(irp, parent=self)
            else:
                log.error('No apropriate input handler!')
                irp.input = None
                irp.complete()

        if _type == 'game_action_apply':
            evt = args[0]
            if hasattr(evt, 'source') and evt.source != evt.target:
                sp = self.player2portrait(evt.source)
                dp = self.player2portrait(evt.target)
                Ray(sp, dp, parent=self, zindex=10)

        if _type == 'game_action_after':
            evt = args[0]
            import effects
            f = effects.mapping.get(evt.__class__)
            if f:
                f(self, evt)
            else:
                log.debug('%s occured!' % evt.__class__.__name__)

        if _type == 'simplegame_begin':
            for port in self.char_portraits:
                p = self.game.players[port.player_index]
                port.life = p.gamedata.life


    def draw(self, dt):
        self.prompt.draw()
        self.draw_subcontrols(dt)
