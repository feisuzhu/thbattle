# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import ui_message, ui_schedule
from client.ui.controls import *
from client.ui import resource as common_res, shaders
import resource as gres
import itertools

from .game_controls import *

from gamepack.thb import actions as thbactions, cards as thbcards
from game.autoenv import Game

from utils import DataHolder, BatchList, IRP

import logging
log = logging.getLogger('THBattleUI_Input')

class Dummy(object):
    '''
    Make the view think the input request will get processed.
    '''
    def __init__(*a, **k):
        pass

class UISelectTarget(Control):

    def __init__(self, irp, *a, **k):
        Control.__init__(self, *a, **k)
        parent = self.parent
        self.irp = irp
        assert isinstance(irp, IRP)

        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

        self.confirmbtn = ConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
            buttons=((u'确定', True), (u'结束', False))
        )
        self.progress_bar = b = BigProgressBar(parent=self, x=0, y=0, width=250)
        b.value = LinearInterp(
            1.0, 0.0, irp.timeout,
            on_done=lambda *a: self.cleanup()
        )
        self.label = lbl = pyglet.text.Label(
            text=u"HEY SOMETHING'S WRONG", x=125, y=28,
            font_size=12, color=(255, 255, 160, 255), bold=True,
            anchor_x='center', anchor_y='bottom'
        )

        @self.confirmbtn.event
        def on_confirm(is_ok):
            irp = self.irp
            irp.input = self.get_result() if is_ok else None
            irp.complete()
            #self.cleanup()
            return

        def dispatch_selection_change():
            self.confirmbtn.buttons[0].state = Button.DISABLED
            self.on_selection_change()

        parent.push_handlers(
            on_selection_change=dispatch_selection_change
        )

        g = Game.getgame()
        port = parent.player2portrait(g.me)
        port.equipcard_area.clear_selection()

        #dispatch_selection_change() # the clear_selection thing will trigger this

    def set_text(self, text):
        self.label.text = text

    def on_selection_change(self):
        # subclasses should surpress it
        self.set_valid()

    def get_result(self): # override this to customize
        #return (skills, players, cards)
        parent = self.parent
        g = Game.getgame()
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

    def on_message(self, _type, *args):
        if _type in ('evt_user_input_timeout', 'evt_user_input_finish'):
            if args[0].player is Game.getgame().me:
                self.cleanup()

class BaseUIChooseCardAndPlayer(UISelectTarget):
    auto_chosen = False
    def __init__(self, irp, *a, **k):
        action, candidates = irp.attachment
        self.action = action

        if self.for_reject:
            ori = self.set_valid
            self._sv_val = False

            def reject_sv():
                self._sv_val = True

            self.set_valid = reject_sv

            def delay(dt):
                self.set_valid = ori
                if self._sv_val: ori()

            pyglet.clock.schedule_once(delay, 0.5)

        UISelectTarget.__init__(self, irp, *a, **k)
        if candidates:
            parent = self.parent
            g = Game.getgame()
            disables = [p for p in g.players if p not in candidates]
            parent.begin_select_player(disables)

    def on_selection_change(self):
        try:
            act, candidates = self.irp.attachment

            g = Game.getgame()
            parent = self.parent
            if not parent: return

            cond = getattr(act, 'cond', False)

            while self.for_reject:
                self._sv_val = False
                self.set_text(u'自动结算好人卡…')
                if not any(cond([c]) for c in itertools.chain(g.me.cards, g.me.showncards)):
                    from gamepack.thb.characters import reimu
                    if not (isinstance(g.me, reimu.Reimu) and not g.me.dead): # HACK: but it works fine
                        self.irp.input = None
                        self.irp.complete()
                        return

                '''
                if isinstance(act.target_act, thbcards.DelayedSpellCardAction):
                    break

                if act.target_act.source is act.target_act.target is g.me:
                    # my sc
                    self.irp.input = None
                    self.irp.complete()
                    return
                if act.target_act.source is g.me and not hasattr(act.target_act, 'parent_action'):
                    # my SC and is not targeting multiple players, target is not me
                    if act.target_act.target is not g.me:
                        self.irp.input = None
                        self.irp.complete()
                        return
                '''
                
                # HACK
                if g.current_turn is not g.me:
                    from .effects import input_snd_prompt
                    input_snd_prompt()

                break

            if cond:
                if not self.auto_chosen:
                    self.auto_chosen = True
                    from itertools import chain
                    for c in chain(g.me.showncards, g.me.cards):
                        if not cond([c]): continue
                        hca = parent.handcard_area
                        for cs in hca.cards:
                            if cs.associated_card == c:
                                break
                        else:
                            raise Exception('WTF?!')
                        hca.toggle(cs, 0.3)
                        return

                skills = parent.get_selected_skills()
                cards = parent.get_selected_cards()
                if skills:
                    for skill_cls in skills:
                        cards = [skill_cls.wrap(cards, g.me)]
                        try:
                            rst, reason = cards[0].ui_meta.is_complete(g, cards)
                        except Exception as e:
                            rst, reason = False, u'[card.ui_meta.is_complete错误]'
                            import traceback
                            traceback.print_exc()

                        if not rst:
                            self.set_text(reason)
                            return

                c = cond(cards)
                c1, text = act.ui_meta.choose_card_text(g, act, cards)
                assert c == c1
                self.set_text(text)

                if not c: return

            if candidates:
                players = parent.get_selected_players()
                players, valid = act.choose_player_target(players)
                try:
                    valid1, reason = act.ui_meta.target(players)
                    assert bool(valid) == bool(valid1)
                except Exception as e:
                    log.exception(e)
                    valid1, reason = valid, u'[act.ui_meta.target错误]'
                parent.set_selected_players(players)
                self.set_text(reason)
                if not valid: return

            self.set_valid()
        except Exception as e:
            import traceback
            traceback.print_exc(e)

    def cleanup(self):
        try:
            hca = self.parent.handcard_area
            for cs in hca.control_list:
                if cs.hca_selected:
                    hca.toggle(cs, 0.3)
        except AttributeError:
            # parent is none, self already deleted
            pass
        UISelectTarget.cleanup(self)

class UIChooseCardAndPlayer(BaseUIChooseCardAndPlayer):
    for_reject = False

class UIChooseCardAndPlayerReject(BaseUIChooseCardAndPlayer):
    for_reject = True

class UIDoActionStage(UISelectTarget):
    # for actions.ActionStage
    #def get_result(self):
    #    pass
    def __init__(self, *a, **k):
        UISelectTarget.__init__(self, *a, **k)

    def on_selection_change(self):
        parent = self.parent
        skills = parent.get_selected_skills()
        cards = parent.get_selected_cards()

        g = Game.getgame()

        if skills:
            cards = [skills[0].wrap(cards, g.me)]
            for skill_cls in skills[1:]:
                try:
                    isc = getattr(cards[0].ui_meta, 'is_complete', None)
                    if not isc:
                        self.set_text(u'您不能像这样组合技能')
                        return
                    rst, reason = isc(g, cards)
                    if not rst:
                        self.set_text(reason)
                        return
                except Exception as e:
                    self.set_text(u'[card.ui_meta.is_complete错误]')
                    import traceback
                    traceback.print_exc()
                    return

                cards = [skill_cls.wrap(cards, g.me)]

        if cards:
            while True:
                if len(cards) != 1: break

                card = cards[0]

                from ..cards import VirtualCard
                if not (
                    card.is_card(VirtualCard) or
                    card.resides_in in (g.me.cards, g.me.showncards)
                ): break

                target_list, tl_valid = card.target(g, g.me, parent.get_selected_players())
                if target_list is not None:
                    parent.set_selected_players(target_list)
                    disables = []
                    # if card.target in (thbcards.t_One, thbcards.t_OtherOne):
                    if card.target.__name__ in ('t_One', 't_OtherOne'):
                        for p in g.players:
                            act = thbactions.ActionStageLaunchCard(g.me, [p], card)
                            if not act.can_fire():
                                disables.append(p)

                    parent.begin_select_player(disables)
                    for i in disables:
                        try:
                            target_list.remove(i)
                        except ValueError:
                            pass

                try:
                    rst, reason = card.ui_meta.is_action_valid(g, cards, target_list)
                except Exception as e:
                    log.exception(e)
                    rst, reason = (True, u'[card.ui_meta.is_action_valid错误]')

                self.set_text(reason)
                if rst:
                    if tl_valid:
                        act = thbactions.ActionStageLaunchCard(g.me, target_list, card)
                        if act.can_fire():
                            self.set_valid()
                        else:
                            self.set_text(u'您不能这样出牌')
                    else:
                        self.set_text(u'您选择的目标不符合规则')
                return

            self.set_text(u'您选择的牌不符合出牌规则')
        else:
            self.set_text(u'请出牌…')

        parent.end_select_player()

class UIChooseGirl(Panel):
    class GirlSelector(ImageSelector, BalloonPrompt):
        def __init__(self, choice, group, *a, **k):

            self.choice = choice
            cc = choice.char_cls
            meta = cc.ui_meta
            pimg = meta.port_image
            self.char_name = meta.char_name
            self.char_maxlife = cc.maxlife

            ImageSelector.__init__(
                self, pimg, group,
                *a, **k
            )

            self.init_balloon(meta.description)

        def on_dblclick(self):
            p = self.parent
            c = self.choice
            if not c.chosen and p.can_select:
                irp = p.irp
                assert irp
                irp.input = c.cid
                irp.complete()
                p.end_selection()

    def __init__(self, attachment, *a, **k):
        w, h = 500 + 1*160, 390 + 1*113
        Panel.__init__(self, width=w, height=h, zindex=5, *a, **k)
        p = self.parent
        pw, ph = p.width, p.height
        self.x, self.y = (pw-w)/2, (ph-h)/2
        self.irp = None
        self.can_select = False
        choices = self.choices = [c for c in attachment if c.char_cls and not getattr(c, 'chosen', False)]
        GS = UIChooseGirl.GirlSelector
        self.selectors = selectors = []
        for i, c in enumerate(choices):
            y, x = divmod(i, 4)
            x, y = 15 + 160*x, 45 + 113*(3-y)
            selectors.append(
                GS(c, selectors, parent=self, x=x, y=y)
            )


    def on_message(self, _evt, *args):
        if _evt == 'evt_user_input':
            irp = args[0]
            tag = irp.tag
            if tag == 'choose_girl':
                assert self.irp is None
                self.irp = irp
                self.begin_selection()

        elif _evt == 'evt_choose_girl_end':
            self.cleanup()

        elif _evt == 'evt_girl_chosen':
            choice = args[0]
            for c in self.selectors:
                if c.choice is choice:
                    c.disable()
                    break

    def cleanup(self):
        if self.irp:
            self.irp.input = None
            self.irp.complete()
        self.delete()

    def begin_selection(self):
        self.pbar = BigProgressBar(
            parent=self, x=(self.width-250)//2, y=9, width=250,
        )

        def on_done(*a):
            self.irp.input = None
            self.irp.complete()
            self.end_selection()

        self.pbar.value = LinearInterp(
            1.0, 0.0, self.irp.timeout,
            on_done=on_done,
        )
        self.can_select = True

    def end_selection(self):
        self.can_select = False
        self.irp = None
        self.pbar.delete()

def choose_girl_event_handler(data, parent):
    pl, choices = data
    if Game.getgame().me in pl:
        UIChooseGirl(choices, parent=parent)

class UIChoosePeerCard(Panel):
    lookup = {
        'handcard': u'手牌区',
        'showncard': u'明牌区',
        'equips': u'装备区',
        'fatetell': u'判定区',
    }

    def __init__(self, irp, *a, **k):
        self.irp = irp
        target, categories = irp.attachment
        h = 40 + len(categories)*145 + 10
        w = 100 + 6*93.0+30
        self.lbls = lbls = pyglet.graphics.Batch()

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)

        y = 40

        i = 0
        for cat in reversed(categories):
            if not len(cat):
                h -= 145 # no cards in this category
                continue

            pyglet.text.Label(
                text=self.lookup[cat.type],
                font_name = 'AncientPix', font_size=12,
                color=(255, 255, 160, 255),
                x=30, y=y+62+145*i,
                anchor_x='left', anchor_y='center',
                batch=lbls,
            )
            ca = DropCardArea(
                parent=self,
                x=100, y=y+145*i,
                fold_size=6,
                width=6*93, height=125,
            )
            for c in cat:
                cs = CardSprite(c, parent=ca)
                cs.associated_card = c
                @cs.event
                def on_mouse_dblclick(x, y, btn, mod, cs=cs):
                    irp = self.irp
                    irp.input = cs.associated_card.syncid
                    self.cleanup()
            ca.update()
            i += 1

        p = self.parent
        self.x, self.y = (p.width - w)//2, (p.height - h)//2
        self.width, self.height = w, h
        self.update()

        self.progress_bar = b = BigProgressBar(
            parent=self, x=(w-250)//2, y=7, width=250
        )
        b.value = LinearInterp(
            1.0, 0.0, irp.timeout,
            on_done=lambda *a: self.cleanup()
        )

        btn = ImageButton(
            common_res.buttons.close_blue,
            parent=self,
            x=w-20, y=h-20,
        )

        @btn.event
        def on_click():
            self.irp.input = None
            self.cleanup()

    def draw(self):
        Panel.draw(self)
        with shaders.FontShadow as fs:
            fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.9)
            self.lbls.draw()

    def cleanup(self):
        self.irp.complete()
        self.delete()

    def on_message(self, _type, *args):
        if _type == 'evt_user_input_timeout':
            self.cleanup()

class UIChooseOption(Control):

    def __init__(self, irp, *a, **k):
        Control.__init__(self, *a, **k)
        parent = self.parent
        self.irp = irp
        assert isinstance(irp, IRP)

        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

        try:
            ui_meta = irp.attachment.ui_meta
            choose_option_buttons = ui_meta.choose_option_buttons
            choose_option_prompt = ui_meta.choose_option_prompt
        except AttributeError:
            choose_option_buttons = ((u'确定', True), (u'结束', False))
            choose_option_prompt = u'UIChooseOption: %s missing ui_meta' % (
                irp.attachment.__class__.__name__
            )

        self.confirmbtn = ConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
            buttons=choose_option_buttons
            #buttons=((u'出牌', True), (u'取消出牌', False))
        )
        self.progress_bar = b = BigProgressBar(parent=self, x=0, y=0, width=250)
        b.value = LinearInterp(
            1.0, 0.0, irp.timeout,
            on_done=lambda *a: self.cleanup()
        )
        self.label = lbl = pyglet.text.Label(
            text=choose_option_prompt, x=125, y=28,
            font_size=12, color=(255, 255, 160, 255), bold=True,
            anchor_x='center', anchor_y='bottom'
        )

        @self.confirmbtn.event
        def on_confirm(val):
            irp = self.irp
            irp.input = val
            irp.complete()
            self.cleanup()
            return

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def cleanup(self):
        self.irp.complete()
        self.delete()

    def draw(self):
        self.draw_subcontrols()
        from client.ui import shaders
        with shaders.FontShadow as fs:
            fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.7)
            self.label.draw()

    def on_message(self, _type, *args):
        if _type == 'evt_user_input_timeout':
            self.cleanup()

class UIChooseIndividualCard(Panel):
    def __init__(self, irp, *a, **k):
        self.irp = irp
        cards = irp.attachment
        cw = min(6, len(cards)) * 93
        h = 30 + 145 + 10
        w = 30 + cw + 30

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)

        ca = DropCardArea(
            parent=self,
            x=30, y=30,
            fold_size=6,
            width=cw, height=125,
        )
        for c in cards:
            cs = CardSprite(c, parent=ca)
            cs.associated_card = c
            @cs.event
            def on_mouse_dblclick(x, y, btn, mod, cs=cs):
                irp = self.irp
                irp.input = cs.associated_card.syncid
                self.cleanup()
        ca.update()

        p = self.parent
        self.x, self.y = (p.width - w)//2, (p.height -h)//2
        self.width, self.height = w, h
        self.update()

        btn = ImageButton(
            common_res.buttons.close_blue,
            parent=self,
            x=w-20, y=h-20,
        )

        @btn.event
        def on_click():
            self.irp.input = None
            self.cleanup()

    def cleanup(self):
        self.irp.complete()
        self.delete()

    def on_message(self, _type, *args):
        if _type == 'evt_user_input_timeout':
            self.cleanup()

class UIHarvestChoose(Panel):
    def __init__(self, cards, *a, **k):
        w = 20 + (91+10)*4 + 20
        h = 20 + 125 + 20 + 125 + 20 + 20

        self.lbl = lbl = pyglet.text.Label(
            text=u"等待玩家的其他操作", x=w//2, y=300,
            font_size=12, color=(255, 255, 160, 255), bold=True,
            anchor_x='center', anchor_y='bottom'
        )

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)
        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2 + 20
        self.width, self.height = w, h
        self.update()

        self.mapping = mapping = {}
        self.irp = None
        for i, c in enumerate(cards):
            y, x = divmod(i, 4)
            x, y = 20 + (91+10)*x, 20 +(125+20)*(1-y)
            cs = CardSprite(c, parent=self, x=x, y=y)
            cs.associated_card = c
            mapping[id(c)] = cs
            @cs.event
            def on_mouse_dblclick(x, y, button, modifier, cs=cs):
                if not cs.gray:
                    irp = self.irp
                    if irp:
                        irp.input = cs.associated_card.syncid
                        irp.complete()
                        self.irp = None

    def draw(self):
        Panel.draw(self)
        with shaders.FontShadow as fs:
            fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.9)
            self.lbl.draw()

    def on_message(self, _type, *args):
        if _type == 'evt_harvest_finish':
            self.cleanup()
        elif _type == 'evt_user_input_start':
            irp = args[0]
            if irp.tag == 'harvest_choose':
                self.lbl.text = u'等待%s选择卡牌' % (irp.player.ui_meta.char_name)
                self.lbl.color = (255, 255, 160, 255)
        elif _type == 'evt_user_input_finish':
            irp = args[0]
            if irp.tag == 'harvest_choose':
                self.lbl.text = u'等待玩家的其他操作'
                self.lbl.color = (255, 255, 160, 255)

        elif _type == 'evt_user_input':
            irp = args[0]
            if irp.tag == 'harvest_choose':
                self.irp = irp
                self.lbl.text = u'请你选择一张卡牌'
                self.lbl.color = (160, 251, 255, 255)
        elif _type == 'evt_harvest_choose':
            self.mapping[id(args[0])].gray = True

    def cleanup(self):
        if self.irp:
            self.irp.complete()
        self.delete()

class RanProphetControl(Control):
    dragging = False
    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.width, self.height = 5*95, 280

    def update(self):
        for j, l in enumerate([self.downcards, self.upcards]):
            for i, cs in enumerate(l):
                nx, ny = self._to_loc(i, j)
                cs.x = SineInterp(cs.x, nx, 0.3)
                cs.y = SineInterp(cs.y, ny, 0.3)

    def init(self):
        self.upcards = self.control_list[:]
        for cs in self.upcards:
            cs.zindex = 0
        self.downcards = []
        self.update()
        self.cur_zindex = 1

    def on_mouse_press(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        if c:
            self.dragging = True
            self.sprite = c

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        if not self.dragging: return
        c = self.sprite
        ni = self._to_index(x, y)
        cx, cy = getinterp(c, 'x'), getinterp(c, 'y')
        if isinstance(cx, AbstractInterp): cx = cx._to
        if isinstance(cy, AbstractInterp): cy = cy._to

        oi = self._to_index(cx+45, cy+62)
        if oi != ni:
            c.zindex = self.cur_zindex
            self.cur_zindex += 1
            ll = [self.downcards, self.upcards]
            ll[oi[1]].remove(c)
            ll[ni[1]].insert(ni[0], c)
            self.update()

    def on_mouse_release(self, x, y, btn, modifier):
        self.dragging = False

    def _to_index(self, x, y):
        return int(x / 95), int(y / 155)

    def _to_loc(self, i, j):
        return i*95, j*155

    def get_result(self):
        return (self.upcards, self.downcards)

    def draw(self):
        self.draw_subcontrols()

class UIRanProphet(Panel):
    def __init__(self, irp, parent, *a, **k):
        self.irp = irp
        cards = irp.attachment
        h = 60 + 50 + 280
        w = 100 + 95*5 + 20

        x, y = (parent.width - w)//2, (parent.height -h)//2

        lbls = pyglet.graphics.Batch()
        def lbl(text, x, y):
            pyglet.text.Label(
                text=text,
                font_name = 'AncientPix', font_size=12,
                color=(255, 255, 160, 255),
                x=x, y=y,
                anchor_x='center', anchor_y='center',
                batch=lbls,
            )
        lbl(u'牌堆底', 50, 122)
        lbl(u'牌堆顶', 50, 277)
        lbl(u'请拖动调整牌的位置', w//2, h-25)
        self.lbls = lbls

        Panel.__init__(
            self, x=x, y=y, width=w, height=h, zindex=5, parent=parent,
            *a, **k
        )

        self.rpc = rpc = RanProphetControl(parent=self, x=100, y=60)
        for i, c in enumerate(cards):
            cs = CardSprite(c, parent=rpc)
            cs.associated_card = c
            cs.card_index = i
        rpc.init()

        btn = Button(parent=self, caption=u'调整完成', x=w-120, y=15, width=100, height=30)
        @btn.event
        def on_click():
            self.cleanup()

        b = BigProgressBar(
            parent=self, x=100, y=15, width=250,
        )
        b.value = LinearInterp(
            1.0, 0.0, irp.timeout,
            on_done=self.cleanup,
        )

    def on_message(self, _type, *args):
        if _type == 'evt_user_input_timeout':
            self.cleanup()

    def cleanup(self, *a, **k):
        up, down = self.rpc.get_result()
        up = [c.card_index for c in up]
        down = [c.card_index for c in down]
        self.irp.input = [up, down]
        self.irp.complete()
        self.delete()

    def draw(self):
        Panel.draw(self)
        with shaders.FontShadow as fs:
            fs.uniform.shadow_color = (0.0, 0.0, 0.0, 0.9)
            self.lbls.draw()

mapping = dict(
    choose_card_and_player=UIChooseCardAndPlayer,
    choose_card_and_player_reject=UIChooseCardAndPlayerReject,
    action_stage_usecard=UIDoActionStage,
    choose_girl=Dummy,
    choose_peer_card=UIChoosePeerCard,
    choose_option=UIChooseOption,
    choose_individual_card=UIChooseIndividualCard,
    harvest_choose=Dummy,
    ran_prophet=UIRanProphet,
)

mapping_all = dict(
)

mapping_event = dict(
    harvest_cards=UIHarvestChoose,
    choose_girl_begin=choose_girl_event_handler,
)



def handle_event(self, _type, data):
    if _type == 'user_input':
        irp = data
        itype = irp.tag
        cls = mapping.get(itype)
        if cls:
            self.update_skillbox()
            cls(irp, parent=self)
        else:
            log.error('No appropriate input handler!')
            irp.input = None
            irp.complete()
    elif _type == 'user_input_all_begin':
        pl, tag, attachment = data
        cls = mapping_all.get(tag)
        if cls and Game.getgame().me in pl:
            cls(attachment=attachment, parent=self)
    else:
        cls = mapping_event.get(_type)
        if cls:
            cls(data, parent=self)
