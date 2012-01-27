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

class InputController(Control):
    def on_message(self, _type, *args):
        if _type == 'io_timeout':
            self.cleanup()

class UIChoose1CardAnd1Char(InputController):
    def __init__(self, irp, *a, **k):
        InputController.__init__(self, *a, **k)
        self.irp = irp
        parent = self.parent
        self.btn_ok = Button(
            parent=self, caption=u'确定', x=0, y=0, width=80, height=30
        )
        self.btn_cancel = Button(
            parent=self, caption=u'取消', x=97, y=0, width=80, height=30
        )

        self.x, self.y, self.width, self.height = 333, 202, 250, 30

        self.input_player = None
        '''
        def choose_multiple_char(x, y, button, modifier):
            c = parent.control_frompoint1(x, y)
            if isinstance(c, GameCharacterPortrait):
                c.selected = not c.selected
                if c.selected:
                    self.input_players.append(c.player_index)
                else:
                    self.input_players.remove(c.player_index)
        '''

        def choose_1char(x, y, button, modifier):
            c = parent.control_frompoint1(x, y)
            if isinstance(c, GameCharacterPortrait):
                sel = c.selected
                self.input_player = c.player_index
                for p in parent.char_portraits:
                    p.selected = False
                c.selected = not sel
            return True

        parent.push_handlers(
            on_mouse_click=choose_1char,
        )

        def _cleanup():
            for c in parent.char_portraits:
                c.selected = False
            parent.pop_handlers()
            self.delete()

        self.cleanup = _cleanup

        @self.btn_ok.event
        def on_click():
            irp = self.irp
            try:
                ci = parent.handcard_area.selected.index(True)
                irp.input = [ci, self.input_player]
            except IndexError:
                irp.input = None
            irp.complete()
            _cleanup()

        @self.btn_cancel.event
        def on_click():
            irp = self.irp
            irp.input = None
            irp.complete()
            _cleanup()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

class UIChooseCards(InputController):
    def __init__(self, irp, *a, **k):
        InputController.__init__(self, *a, **k)
        self.irp = irp
        parent = self.parent
        self.btn_ok = Button(
            parent=self, caption=u'确定', x=0, y=0, width=80, height=30
        )
        self.btn_cancel = Button(
            parent=self, caption=u'取消', x=97, y=0, width=80, height=30
        )

        self.x, self.y, self.width, self.height = 333, 202, 250, 30

        def _cleanup():
            self.delete()

        self.cleanup = _cleanup

        @self.btn_ok.event
        def on_click():
            irp = self.irp
            card_indices = [i for i, c in enumerate(parent.handcard_area.selected) if c]
            irp.input = card_indices
            irp.complete()
            _cleanup()

        @self.btn_cancel.event
        def on_click():
            irp = self.irp
            irp.input = None
            irp.complete()
            _cleanup()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

mapping = dict(
    choose_card=UIChooseCards,
    action_stage_usecard=UIChoose1CardAnd1Char,
)
