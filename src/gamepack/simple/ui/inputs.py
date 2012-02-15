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

import logging
log = logging.getLogger('SimpleGameUI_Input')

class InputController(Control):
    def on_message(self, _type, *args):
        if _type == 'evt_user_input_timeout':
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
            self.irp.complete()
            self.delete()

        self.cleanup = _cleanup

        @self.btn_ok.event
        def on_click():
            irp = self.irp
            try:
                cid = None
                for cs in parent.handcard_area.cards:
                    if cs.hca_selected:
                        cid = cs.associated_card.syncid
                        break
                irp.input = [cid, [self.input_player]]
            except ValueError:
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
            self.irp.complete()
            self.delete()

        self.cleanup = _cleanup

        @self.btn_ok.event
        def on_click():
            irp = self.irp
            cid_list = [
                cs.associated_card.syncid
                for cs in parent.handcard_area.cards
                if cs.hca_selected
            ]
            irp.input = cid_list
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

class UISelectTarget(InputController):
    sel_players = 1 # num of players to select

    def __init__(self, irp, *a, **k):
        InputController.__init__(self, *a, **k)
        parent = self.parent
        self.irp = irp

        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

        parent.begin_select_player(self.sel_players)

        self.confirmbtn = ConfirmButtons(parent=self, x=259, y=4, width=165, height=24)
        self.progress_bar = b = BigProgressBar(parent=self, x=0, y=0, width=250)
        b.value = LinearInterp(1.0, 0.0, irp.timeout, on_done=self.cleanup)
        self.label = lbl = pyglet.text.Label(
            text=u'请选择…', x=88, y=28,
            font_size=12, color=(255,255,180,255), bold=True,
            anchor_x='center', anchor_y='center'
        )

        @self.confirmbtn.event
        def on_confirm(is_ok):
            irp = self.irp
            irp.input = self.get_result() if is_ok else None
            irp.complete()
            self.cleanup()
            return
            # ------------------------
            if is_ok:

                irp.input = cid_list
            else:
                irp.input = None

            irp.complete()
            self.cleanup()

        def dispatch_selection_change():
            self.dispatch_event('on_selection_change')

        parent.handcard_area.push_handlers(
            on_selection_change=dispatch_selection_change
        )

        parent.push_handlers(
            on_player_selection_change=dispatch_selection_change
        )

    def set_text(self, text):
        self.label.text = text

    def on_selection_change(self):
        # subclasses should surpress it
        self.confirmbtn.buttons[0].disabled = False

    def get_result(self): # override this to customize
        #return (skill, players, cards)
        cid_list = [
            cs.associated_card.syncid
            for cs in parent.handcard_area.cards
            if cs.hca_selected
        ]
        g = self.game
        pid_list = [
            g.get_playerid(p)
            for p in self.parent.get_selected_players()
        ]
        return (None, pid_list, cid_list)

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def cleanup(self):
        p = self.parent
        p.end_select_player()
        p.pop_handlers()
        p.handcard_area.pop_handlers()
        self.irp.complete()
        self.delete()

UISelectTarget.register_event_type('on_selection_change')

'''
class UIChooseCards(UISelectTarget):
    sel_players = 0
'''


mapping = dict(
    choose_card=UIChooseCards,
    action_stage_usecard=UIChoose1CardAnd1Char,
)
