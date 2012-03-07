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

class UISelectTarget(InputController):

    def __init__(self, irp, *a, **k):
        InputController.__init__(self, *a, **k)
        parent = self.parent
        self.irp = irp

        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

        self.confirmbtn = ConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
            buttons=((u'出牌', True), (u'取消出牌', False))
        )
        self.progress_bar = b = BigProgressBar(parent=self, x=0, y=0, width=250)
        b.value = LinearInterp(
            1.0, 0.0, irp.timeout,
            on_done=lambda *a: self.cleanup()
        )
        self.label = lbl = pyglet.text.Label(
            text=u'请选择…', x=125, y=28,
            font_size=12, color=(255, 255, 160, 255), bold=True,
            anchor_x='center', anchor_y='bottom'
        )

        @self.confirmbtn.event
        def on_confirm(is_ok):
            irp = self.irp
            irp.input = self.get_result() if is_ok else None
            irp.complete()
            self.cleanup()
            return

        def dispatch_selection_change():
            self.confirmbtn.buttons[0].state = Button.DISABLED
            self.on_selection_change()

        parent.push_handlers(
            on_selection_change=dispatch_selection_change
        )

        dispatch_selection_change()

    def set_text(self, text):
        self.label.text = text

    def on_selection_change(self):
        # subclasses should surpress it
        self.set_valid()

    def get_result(self): # override this to customize
        #return (skills, players, cards)
        parent = self.parent
        g = parent.game
        skills = g.me.skills

        sid_list = [
            skills.index(s)
            for s in parent.get_selected_skills()
        ]

        cid_list = [
            c.syncid
            for c in parent.get_selected_cards()
        ]

        pid_list = [
            g.get_playerid(p)
            for p in parent.get_selected_players()
        ]
        return [sid_list, cid_list, pid_list]

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def cleanup(self):
        p = self.parent
        p.end_select_player()
        p.pop_handlers()
        self.irp.complete()
        self.delete()

    def set_valid(self):
        self.confirmbtn.buttons[0].state = Button.NORMAL

    def draw(self):
        self.draw_subcontrols()
        from client.ui import shaders
        with shaders.FontShadow as fs:
            fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.7)
            self.label.draw()

class UIChooseCards(UISelectTarget):
    # for actions.ChooseCard
    sel_players = 0

    def get_result(self):
        sid_list, cid_list, _  = UISelectTarget.get_result(self)
        return sid_list, cid_list

    def on_selection_change(self):
        act = self.irp.attachment
        skills = self.parent.get_selected_skills()
        cards = self.parent.get_selected_cards()

        g = self.parent.game
        if skills:
            for s in skills:
                cls = s.associated_action
                a = cls(g.me, cards)
                a.apply_action()
                cards = a.cards
                if not cards: break

        if cards:
            if act.cond(cards):
                self.set_text(act.ui_meta.text_valid)
                self.set_valid()
            else:
                self.set_text(u'您选择的牌不符合出牌规则')
        else:
            self.set_text(act.ui_meta.text)
        return True

class UIDoActionStage(UISelectTarget):
    # for actions.ActionStage
    last_card = None
    #def get_result(self):
    #    pass

    def on_selection_change(self):
        parent = self.parent
        skills = parent.get_selected_skills()
        cards = parent.get_selected_cards()

        g = parent.game
        if skills:
            for s in skills:
                cls = s.associated_action
                a = cls(g.me, cards)
                a.apply_action()
                cards = a.cards
                if not cards: break

        if cards:
            while True:
                if len(cards) != 1: break

                card = cards[0]

                source = parent.game.me
                t = card.target
                if t == 'self':
                    target_list = [source]
                elif isinstance(t, int):
                    if self.last_card != card:
                        parent.begin_select_player(t)
                        self.last_card = card
                    target_list = parent.get_selected_players()
                else:
                    # for cards like GrazeCard
                    # to display customized prompt string
                    target_list = None

                action_cls = card.associated_action
                if action_cls:
                    rst, reason = action_cls.ui_meta.is_action_valid(source, cards, target_list)
                else:
                    rst, reason = False, getattr(card.ui_meta, 'passive_card_prompt', 'UNDEFINED')

                self.set_text(reason)
                if rst: self.set_valid()
                return

            self.set_text(u'您选择的牌不符合出牌规则')
            parent.end_select_player()
            self.last_card = None
        else:
            parent.end_select_player()
            self.set_text(u'请出牌…')
            self.last_card = None

mapping = dict(
    choose_card=UIChooseCards,
    action_stage_usecard=UIDoActionStage,
)
