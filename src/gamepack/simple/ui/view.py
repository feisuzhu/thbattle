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

import effects, inputs

class UIEventHook(EventHandler):

    def evt_user_input(self, input):
        irp = IRP()
        irp.input = None
        irp.attachment = input.attachment
        irp.tag = input.tag
        ui_message('evt_user_input', irp)
        irp.wait()
        input.input = irp.input
        return input

    # evt_user_input_timeout

    def handle(self, evt, data):
        name = 'evt_%s' % evt
        if hasattr(self, name):
            return getattr(self, name)(data)
        else:
            ui_message(name, data)
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

        self.label_prompt = pyglet.text.Label(
            text='youmu youmu youmu', font_size=20, color=(0,0,0,255),
            x=280, y=413, anchor_y = 'bottom'
        )

        self.handcard_area = HandCardArea(
            parent=self, x=238, y=13, zindex=3,
        )

        self.dropcard_area = DropCardArea(
            parent=self, x=0, y=324, zindex=3,
        )

        self.animations = pyglet.graphics.Batch()

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
        if _type == 'evt_user_input':
            irp = args[0]
            itype = irp.tag
            self.label_prompt.text = itype
            cls = inputs.mapping.get(itype)
            if cls:
                cls(irp, parent=self)
            else:
                log.error('No apropriate input handler!')
                irp.input = None
                irp.complete()

        elif _type == 'evt_simplegame_begin':
            for port in self.char_portraits:
                p = self.game.players[port.player_index]
                port.life = p.gamedata.life

        elif _type == 'evt_player_turn':
            self.current_turn = args[0]

        if _type.startswith('evt_'):
            effects.handle_event(self, _type[4:], args[0])

    def draw(self, dt):
        self.label_prompt.draw()
        self.draw_subcontrols(dt)
        self.animations.draw()

    def ray(self, f, t):
        if f == t: return
        sp = self.player2portrait(f)
        dp = self.player2portrait(t)
        x0, y0 = sp.x + sp.width/2, sp.y + sp.height/2
        x1, y1 = dp.x + dp.width/2, dp.y + dp.height/2
        Ray(x0, y0, x1, y1, parent=self, zindex=10)

    def prompt(self, s):
        self.parent.events_box.append(unicode(s)+u'\n')
