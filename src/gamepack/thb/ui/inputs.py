# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import message as ui_message
from client.ui.base import schedule as ui_schedule
from client.ui.controls import *
from client.ui import resource as common_res
import resource as gres

from gamepack.thb import actions
from game.autoenv import Game

from utils import DataHolder

import logging
log = logging.getLogger('THBattleUI_Input')

class InputController(Control):
    def on_message(self, _type, *args):
        if _type == 'evt_user_input_timeout':
            self.cleanup()

class Dummy(object):
    '''
    Make the view think the input request will get processed.
    '''
    def __init__(*a, **k):
        pass

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

class UIChooseMyCards(UISelectTarget):
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
            for skill_cls in skills:
                cards = [skill_cls(g.me, cards)]

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
    def __init__(self, *a, **k):
        self.dist_calc = None
        UISelectTarget.__init__(self, *a, **k)
        irp = self.irp

        def get_distance():
            # will be called from Game greenlet
            g = Game.getgame()
            calc = actions.CalcDistance(g.me)
            self.dist_calc = calc
            ui_schedule(self.on_selection_change)

        irp.do_callback(get_distance)

    def on_selection_change(self):
        parent = self.parent
        if not parent:
            # if user close this too fast,
            # the bottom half (get_distance thing) will execute after
            # self been deleted.
            return
        skills = parent.get_selected_skills()
        cards = parent.get_selected_cards()

        if not self.dist_calc: return

        g = parent.game
        if skills:
            for skill_cls in skills:
                cards = [skill_cls(g.me, cards)]

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

                rst, reason = card.ui_meta.is_action_valid(cards, source, target_list)

                self.set_text(reason)
                if rst:
                    def gameengine_check():
                        g = Game.getgame()
                        act = actions.LaunchCard(g.me, target_list, card)
                        if act.can_fire():
                            ui_schedule(self.set_valid)
                        else:
                            ui_schedule(self.set_text, u'您不能这样出牌')

                    self.irp.do_callback(gameengine_check)

                return

            self.set_text(u'您选择的牌不符合出牌规则')
            self.last_card = None
        else:

            self.set_text(u'请出牌…')
            self.last_card = None

        parent.end_select_player()

class UIChooseGirl(Panel):
    class GirlSelector(Control):
        hover_alpha = InterpDesc('_hover_alpha')
        auxfbo = Framebuffer()
        def __init__(self, choice, *a, **k):
            Control.__init__(
                self, width=145, height=98,
                *a, **k
            )
            self.draw_frame = False
            self.hover_alpha = 0.0
            self.choice = choice
            cc = choice.char_cls
            meta = cc.ui_meta
            pimg = self.port_image = meta.port_image
            self.char_name = meta.char_name
            self.char_maxlife = cc.maxlife

            # TODO: name and maxlife
            self.grayed_image = pyglet.image.Texture.create_for_size(
                GL_TEXTURE_RECTANGLE_ARB, pimg.width, pimg.height, GL_RGBA
            )

        def on_mouse_enter(self, x, y):
            self.hover_alpha = 0.4

        def on_mouse_leave(self, x, y):
            self.hover_alpha = LinearInterp(
                0.4, 0, 0.3
            )

        def on_mouse_click(self, x, y, button, modifier):
            for gs in self.parent.girl_selectors:
                gs.draw_frame = False
            self.draw_frame = True

        def on_mouse_dblclick(self, x, y, button, modifier):
            p = self.parent
            c = self.choice
            if not c.chosen and p.can_select:
                irp = p.irp
                assert irp
                irp.input = c.cid
                irp.complete()
                p.end_selection()

        def draw(self):
            glColor3f(1, 1, 1)
            if self.choice.chosen:
                self.grayed_image.blit(0, 0)
            else:
                self.port_image.blit(0, 0)

            glColor3f(0.757, 1.0, 0.384)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glRectf(0, 0, self.width, self.height)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            if self.draw_frame:
                common_res.choosegirl_shine.blit(-11, -11)

            a = self.hover_alpha
            if a:
                glColor4f(1, 1, 0.8, a)
                glRectf(0, 0, self.width, self.height)

    def __init__(self, attachment, *a, **k):
        w, h = 500, 360
        Panel.__init__(self, width=w, height=h, *a, **k)
        p = self.parent
        pw, ph = p.width, p.height
        self.x, self.y = (pw-w)/2, (ph-h)/2
        self.irp = None
        self.can_select = False
        choices = self.choices = [c for c in attachment if c.char_cls]
        assert len(choices) == 9
        GS = UIChooseGirl.GirlSelector
        self.girl_selectors = self.control_list
        for i, c in enumerate(choices):
            y, x = divmod(i, 3)
            x, y = 15 + 160*x, 15 + 113*y
            GS(parent=self, choice=c, x=x, y=y)

    def on_message(self, _evt, *args):
        if _evt == 'evt_user_input':
            irp = args[0]
            tag = irp.tag
            if tag == 'choose_girl':
                assert self.irp is None
                self.irp = irp
                self.begin_selection()
        elif _evt == 'girl_chosen':
            c = args[0]
            if c.char_cls: return # choice of the other force
            port = self.parent.player2portrait(p)
            meta = c.char_cls.ui_meta
            port.port_image = meta.port_image
            port.char_name = meta.char_name
            port.update()
        elif _evt == 'evt_user_input_all_end':
            tag = args[0]
            if tag == 'choose_girl':
                self.cleanup()

    def cleanup(self):
        if self.irp:
            self.irp.input = None
            self.irp.complete()
        self.delete()

    def begin_selection(self):
        self.can_select = True

    def end_selection(self):
        self.can_select = False
        self.irp = None


mapping = dict(
    choose_card=UIChooseMyCards,
    action_stage_usecard=UIDoActionStage,
    choose_girl=Dummy,
)

mapping_all = dict(
    choose_girl=UIChooseGirl,
)
