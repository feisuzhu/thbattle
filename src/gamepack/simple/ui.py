# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Button, TextBox, Control, message as ui_message
from client.ui.controls_extra import *
from utils import IRP

from game.autoenv import EventHandler, Action, GameError

class UIEventHook(EventHandler):
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
        self.textbox = TextBox(parent=self, x=248, y=255, width=336, text='[0, 0]')
        self.prompt = pyglet.text.Label(
            text='youmu youmu youmu', font_size=20, color=(0,0,0,255),
            x=280, y=413, anchor_y = 'bottom'
        )

        @self.btn_ok.event
        def on_click():
            self.btn_ok.state = Button.DISABLED
            self.btn_cancel.state = Button.DISABLED
            irp = self.irp
            irp.input = eval(self.textbox.text)
            irp.complete()

        @self.btn_cancel.event
        def on_click():
            self.btn_ok.state = Button.DISABLED
            self.btn_cancel.state = Button.DISABLED
            irp = self.irp
            irp.input = None
            irp.complete()

    def on_message(self, _type, *args):
        if _type.startswith('input_'):
            self.irp = args[0]
            self.btn_ok.state = Button.NORMAL
            self.btn_cancel.state = Button.NORMAL
            self.prompt.text = _type[6:]

    def draw(self, dt):
        self.prompt.draw()
        self.draw_subcontrols(dt)
