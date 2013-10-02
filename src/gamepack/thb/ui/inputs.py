# -*- coding: utf-8 -*-

import itertools
import logging
import math
import random

log = logging.getLogger('THBattleUI_Input')

import pyglet

from game.autoenv import Game
from gamepack.thb import actions as thbactions
from gamepack.thb.cards import CardList, RejectHandler

from pyglet.text import Label

from client.ui.controls import BalloonPromptMixin, BigProgressBar
from client.ui.controls import Button, ConfirmButtons, Control
from client.ui.controls import ImageButton, ImageSelector
from client.ui.controls import Panel

from client.ui.base.interp import AbstractInterp, getinterp, InterpDesc, LinearInterp, SineInterp

from client.ui.resource import resource as common_res
from .game_controls import DropCardArea, CardSprite


class InputHandler(object):
    def process_user_input_start(self, ilet):
        pass

    def process_user_input(self, ilet):
        pass

    def process_user_input_finish(self, ilet, rst):
        pass

    def cleanup(self):
        pass


class UISelectTarget(Control, InputHandler):

    def __init__(self, trans, *a, **k):
        Control.__init__(self, *a, **k)
        self.trans = trans
        self.inputlet = None
        self.label = None

        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

    def process_user_input(self, ilet):
        parent = self.parent
        self.confirmbtn = ConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
            buttons=((u'确定', True), (u'结束', False))
        )
        self.progress_bar = BigProgressBar(parent=self, x=0, y=0, width=250)
        self.label = Label(
            text=u"HEY SOMETHING'S WRONG", x=125, y=28, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 179),
            anchor_x='center', anchor_y='bottom',
        )

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

        @self.confirmbtn.event
        def on_confirm(is_ok):
            is_ok and ilet.set_result(*self.get_result())
            ilet.done()
            end_transaction(self.trans)

        self.progress_bar.value = LinearInterp(
            1.0, 0.0, ilet.timeout,
            on_done=lambda *a: on_confirm(False)
        )

        self.inputlet = ilet

    def set_text(self, text):
        self.label.text = text

    def on_selection_change(self):
        # subclasses should surpress it
        self.set_valid()

    def get_result(self):  # override this to customize
        parent = self.parent
        return [
            parent.get_selected_skills(),
            parent.get_selected_cards(),
            parent.get_selected_players(),
        ]

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def cleanup(self):
        if not self.label: return  # processed user_input
        p = self.parent
        p.end_select_player()
        p.pop_handlers()

    def set_valid(self):
        self.confirmbtn.buttons[0].state = Button.NORMAL

    def draw(self):
        self.draw_subcontrols()
        lbl = self.label
        lbl and lbl.draw()


class UIDoPassiveAction(UISelectTarget):
    _auto_chosen = False
    _snd_prompt = False
    _in_auto_reject_delay = False

    def process_user_input(self, ilet):
        UISelectTarget.process_user_input(self, ilet)

        initiator = ilet.initiator
        candidates = ilet.candidates

        g = Game.getgame()
        if isinstance(initiator, RejectHandler):
            ori = self.set_valid
            self._sv_val = False

            def reject_sv():
                self._sv_val = True

            self.set_valid = reject_sv

            def delay(dt):
                self.set_valid = ori
                if self._sv_val: ori()

            pyglet.clock.schedule_once(delay, 0.1 + 0.2 * math.sqrt(g.players.index(g.me)))

        if candidates:
            parent = self.parent
            disables = [p for p in g.players if p not in candidates]
            parent.begin_select_player(disables)

        self.dispatch_event('on_selection_change')

    def on_selection_change(self):
        try:
            ilet = self.inputlet
            if not ilet: return
            if self._in_auto_reject_delay: return

            initiator = ilet.initiator
            candidates = ilet.candidates

            g = Game.getgame()
            parent = self.parent
            if not parent: return

            cond = getattr(initiator, 'cond', False)

            if isinstance(initiator, RejectHandler):
                self._sv_val = False
                self.set_text(u'自动结算好人卡…')
                if not any(cond([c]) for c in itertools.chain(g.me.cards, g.me.showncards)):
                    from gamepack.thb.characters import reimu
                    if not (isinstance(g.me, reimu.Reimu) and not g.me.dead):  # HACK: but it works fine
                        self._in_auto_reject_delay = True
                        v = 0.3 - math.log(random.random())
                        self.set_text(u'自动结算好人卡(%.2f秒)' % v)

                        def complete(*a):
                            ilet.done()
                            end_transaction(self.trans)

                        pyglet.clock.schedule_once(complete, v)
                        return

            if ilet.categories:
                if not self._auto_chosen:
                    self._auto_chosen = True
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
                c1, text = initiator.ui_meta.choose_card_text(g, initiator, cards)
                assert c == c1
                self.set_text(text)

                if not c: return

            if candidates:
                players = parent.get_selected_players()
                players, valid = initiator.choose_player_target(players)
                try:
                    valid1, reason = initiator.ui_meta.target(players)
                    assert bool(valid) == bool(valid1)
                except Exception as e:
                    log.exception(e)
                    valid1, reason = valid, u'[act.ui_meta.target错误]'
                parent.set_selected_players(players)
                self.set_text(reason)
                if not valid: return

            self.set_valid()
        except Exception:
            import traceback
            traceback.print_exc()

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


class UIDoActionStage(UISelectTarget):
    # for actions.ActionStage
    #def get_result(self):
    #    pass

    def on_selection_change(self):
        parent = self.parent
        skills = parent.get_selected_skills()
        cards = rawcards = parent.get_selected_cards()

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

        if not cards:
            self.set_text(u'请出牌…')
            parent.end_select_player()
            return

        if len(cards) != 1:
            self.set_text(u'请选择一张牌使用')
            parent.end_select_player()
            return

        card = cards[0]

        from ..cards import VirtualCard
        if not card.is_card(VirtualCard):
            if not card.resides_in in (g.me.cards, g.me.showncards):
                self.set_text(u'您选择的牌不符合出牌规则')
                parent.end_select_player()
                return

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
        if not rst:
            return

        if tl_valid:
            act = thbactions.ActionStageLaunchCard(g.me, target_list, card)

            if skills:
                card = thbactions.skill_wrap(g.me, skills, rawcards, no_reveal=True)

            if card and act.can_fire():
                self.set_valid()
            else:
                self.set_text(u'您不能这样出牌')
        else:
            self.set_text(u'您选择的目标不符合规则')


class GirlSelector(ImageSelector, BalloonPromptMixin):
    x = InterpDesc('_x')
    y = InterpDesc('_y')

    def __init__(self, choice, group, x=0, y=0, *a, **k):

        self.choice = choice
        cc = choice.char_cls
        meta = cc.ui_meta
        pimg = meta.port_image
        self.char_name = meta.char_name
        self.char_maxlife = cc.maxlife

        self.x = x
        self.y = y

        ImageSelector.__init__(
            self, pimg, group,
            *a, **k
        )

        self.init_balloon(meta.description)


class UIChooseGirl(Panel, InputHandler):
    def __init__(self, trans, *a, **k):
        self.trans = trans
        g = Game.getgame()
        choices = trans.mapping[g.me]

        w, h = 500 + 1*160, 390 + 1*113
        Panel.__init__(self, width=w, height=h, zindex=5, *a, **k)
        p = self.parent
        pw, ph = p.width, p.height
        self.x, self.y = (pw-w)/2, (ph-h)/2
        self.inputlet = None
        choices = self.choices = [c for c in choices if c.char_cls and not getattr(c, 'chosen', False)]
        self.selectors = selectors = []
        for i, c in enumerate(choices):
            y, x = divmod(i, 4)
            x, y = 15 + 160*x, 45 + 113*(3-y)
            gs = GirlSelector(c, selectors, parent=self, x=x, y=y)

            @gs.event
            def on_dblclick(gs=gs):
                c = gs.choice
                ilet = self.inputlet
                if not c.chosen and ilet:
                    ilet.set_choice(c)
                    ilet.done()
                    self.end_selection()

            selectors.append(gs)

    def process_user_input(self, ilet):
        self.inputlet = ilet
        self.begin_selection()

    def on_girl_chosen(self, choice):
        for c in self.selectors:
            if c.choice is choice:
                c.disable()
                break

        self.parent.update_portraits()

    def begin_selection(self):
        self.pbar = BigProgressBar(
            parent=self, x=(self.width-250)//2, y=9, width=250,
        )

        def on_done(*a):
            self.inputlet.done()
            self.end_selection()

        self.pbar.value = LinearInterp(
            1.0, 0.0, self.inputlet.timeout,
            on_done=on_done,
        )

    def end_selection(self):
        self.inputlet = None
        self.pbar.delete()


class UIChoosePeerCard(Panel, InputHandler):
    def __init__(self, trans, *a, **k):
        self.trans = trans
        self.lbls = pyglet.graphics.Batch()
        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)

    def process_user_input(self, ilet):
        target = ilet.target
        categories = [getattr(target, i) for i in ilet.categories]

        h = 40 + len(categories)*145 + 10
        w = 100 + 6*93.0+30

        y = 40
        i = 0
        for cat in reversed(categories):
            if not len(cat):
                h -= 145  # no cards in this category
                continue

            Label(
                text=CardList.ui_meta.lookup[cat.type], font_size=12,
                color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
                x=30, y=y+62+145*i, anchor_x='left', anchor_y='center',
                batch=self.lbls,
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
                    ilet.set_card(cs.associated_card)
                    ilet.done()
                    end_transaction(self.trans)

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
            1.0, 0.0, ilet.timeout,
            on_done=lambda *a: self.cleanup()
        )

        btn = ImageButton(
            common_res.buttons.close_blue,
            parent=self,
            x=w-20, y=h-20,
        )

        @btn.event
        def on_click():
            ilet.done()

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()


class UIChooseOption(Control, InputHandler):

    def __init__(self, trans, *a, **k):
        Control.__init__(self, *a, **k)
        self.trans = trans
        self.label = None

        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

    def process_user_input(self, ilet):
        try:
            ui_meta = ilet.initiator.ui_meta
            choose_option_buttons = ui_meta.choose_option_buttons
            choose_option_prompt = ui_meta.choose_option_prompt
            if callable(choose_option_prompt):
                choose_option_prompt = choose_option_prompt(ilet.initiator)

        except AttributeError:
            choose_option_buttons = ((u'确定', True), (u'结束', False))
            choose_option_prompt = u'UIChooseOption: %s missing ui_meta' % (
                ilet.initiator.__class__.__name__
            )

        self.confirmbtn = ConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
            buttons=choose_option_buttons
        )
        self.progress_bar = b = BigProgressBar(parent=self, x=0, y=0, width=250)
        b.value = LinearInterp(
            1.0, 0.0, ilet.timeout,
            on_done=lambda *a: on_confirm(None)
        )
        self.label = Label(
            text=choose_option_prompt, x=125, y=28, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 179),
            anchor_x='center', anchor_y='bottom',
        )

        @self.confirmbtn.event
        def on_confirm(val):
            ilet.set_option(val)
            ilet.done()
            end_transaction(self.trans)

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def draw(self):
        self.draw_subcontrols()
        lbl = self.label
        lbl and lbl.draw()


class UIChooseIndividualCard(Panel, InputHandler):
    def __init__(self, trans, *a, **k):
        self.trans = trans
        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)

    def process_user_input(self, ilet):
        cards = ilet.cards

        cw = min(6, len(cards)) * 93
        h = 30 + 145 + 10
        w = 30 + cw + 30

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
                ilet.set_card(cs.associated_card)
                ilet.done()
                end_transaction(self.trans)

        ca.update()

        p = self.parent
        self.x, self.y = (p.width - w)//2, (p.height - h)//2
        self.width, self.height = w, h
        self.update()

        btn = ImageButton(
            common_res.buttons.close_blue,
            parent=self,
            x=w-20, y=h-20,
        )

        @btn.event
        def on_click():
            ilet.done()
            end_transaction(self.trans)


class UIHarvestChoose(Panel, InputHandler):
    def __init__(self, trans, *a, **k):
        self.trans = trans
        cards = trans.cards
        self.inputlet = None

        w = 20 + (91 + 10) * 4 + 20
        h = 20 + 125 + 20 + 125 + 20 + 20

        self.lbl = Label(
            text=u"等待玩家的其他操作", x=w//2, y=300, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
            anchor_x='center', anchor_y='bottom'
        )

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)
        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2 + 20
        self.width, self.height = w, h
        self.update()

        self.mapping = mapping = {}
        for i, c in enumerate(cards):
            y, x = divmod(i, 4)
            x, y = 20 + (91 + 10) * x, 20 + (125 + 20) * (1 - y)
            cs = CardSprite(c, parent=self, x=x, y=y)
            cs.associated_card = c
            mapping[id(c)] = cs

            @cs.event
            def on_mouse_dblclick(x, y, button, modifier, cs=cs):
                if cs.gray: return
                ilet = self.inputlet
                if not ilet: return
                ilet.set_card(cs.associated_card)
                ilet.done()

    def draw(self):
        Panel.draw(self)
        self.lbl.draw()

    def process_user_input_start(self, ilet):
        self.lbl.text = u'等待%s选择卡牌' % (ilet.actor.ui_meta.char_name)
        self.lbl.color = (255, 255, 160, 255)

    def process_user_input(self, ilet):
        assert ilet.actor is Game.getgame().me
        self.inputlet = ilet
        self.lbl.text = u'请你选择一张卡牌'
        self.lbl.color = (160, 251, 255, 255)

    def process_user_input_finish(self, ilet, rst):
        self.lbl.text = u'等待玩家的其他操作'
        self.lbl.color = (255, 255, 160, 255)
        self.inputlet = None

    def on_harvest_choose(self, card):
        self.mapping[id(card)].gray = True


class Dragger(Control):
    dragging = False

    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.width, self.height = self.expected_size()

    @classmethod
    def expected_size(cls):
        return (
            (cls.item_width + 4) * cls.cols,
            (cls.item_height + 15) * cls.rows,
        )

    def update(self):
        for j, l in enumerate(reversed(self.sprites)):
            for i, cs in enumerate(l):
                nx, ny = self._to_loc(i, j)
                cs.x = SineInterp(cs.x, nx, 0.3)
                cs.y = SineInterp(cs.y, ny, 0.3)
                self.update_sprite(cs, i, j)

    def update_sprite(self, cs, i, j):
        pass

    def init(self):
        self.sprites = [list() for i in xrange(self.rows)]
        self.sprites[0] = self.control_list[:]
        for cs in self.sprites[0]:
            cs.zindex = 0
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

        oi = self._to_index(cx + self.item_width // 2, cy + self.item_height // 2)
        if oi != ni:
            c.zindex = self.cur_zindex
            self.cur_zindex += 1
            ll = list(reversed(self.sprites))
            ll[oi[1]].remove(c)
            ll[ni[1]].insert(ni[0], c)
            self.update()

    def on_mouse_release(self, x, y, btn, modifier):
        self.dragging = False

    def _to_index(self, x, y):
        return int(x / (self.item_width + 4)), int(y / (self.item_height + 30))

    def _to_loc(self, i, j):
        return i * (self.item_width + 4), j * (self.item_height + 30)

    def draw(self):
        self.draw_subcontrols()

    def get_result(self):
        return self.sprites


class RanProphetControl(Dragger):
    cols, rows = 5, 2
    item_width, item_height = 91, 125


class UIRanProphet(Panel, InputHandler):
    def __init__(self, trans, parent, *a, **k):
        Panel.__init__(
            self, x=1, y=1, width=1, height=1, zindex=5, parent=parent,
            *a, **k
        )
        self.lbls = pyglet.graphics.Batch()
        self.trans = trans

    def process_user_input(self, ilet):
        cards = ilet.cards

        w, h = RanProphetControl.expected_size()
        w = 100 + w + 20
        h = 60 + h + 50

        def lbl(text, x, y):
            Label(
                text=text, x=x, y=y, font_size=12,
                anchor_x='center', anchor_y='center',
                color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
                batch=self.lbls,
            )

        lbl(u'牌堆底', 50, 122)
        lbl(u'牌堆顶', 50, 277)
        lbl(u'请拖动调整牌的位置', w//2, h-25)

        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2
        self.width, self.height = w, h
        self.update()

        self.rpc = rpc = RanProphetControl(parent=self, x=100, y=60)
        for i, c in enumerate(cards):
            cs = CardSprite(c, parent=rpc)
            cs.associated_card = c

        rpc.init()

        btn = Button(parent=self, caption=u'调整完成', x=w-120, y=15, width=100, height=30)

        @btn.event
        def on_click(*a):
            up, down = self.rpc.get_result()
            up = [c.associated_card for c in up]
            down = [c.associated_card for c in down]
            ilet.set_result(up, down)
            ilet.done()
            end_transaction(self.trans)

        b = BigProgressBar(parent=self, x=100, y=15, width=250)
        b.value = LinearInterp(1.0, 0.0, ilet.timeout, on_done=on_click)

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()


class KOFSorterControl(Dragger):
    cols, rows = 5, 1
    item_width, item_height = 145, 96

    def update_sprite(self, c, i, j):
        c.disable() if i >= 3 else c.enable()


class UIKOFCharacterSorter(Panel, InputHandler):
    def __init__(self, trans, parent, *a, **k):
        self.trans = trans
        self.lbls = pyglet.graphics.Batch()
        Panel.__init__(
            self, x=1, y=1, width=1, height=1, zindex=5, parent=parent,
            *a, **k
        )

    def process_user_input(self, ilet):
        g = Game.getgame()
        me = g.me
        choices = ilet.mapping[me]
        for i, c in enumerate(choices):
            c._choice_index = i

        w, h = KOFSorterControl.expected_size()
        w = 20 + w + 20
        h = 60 + h + 50

        def lbl(text, x, y):
            Label(
                text=text, font_size=12, x=x, y=y,
                color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 190),
                anchor_x='center', anchor_y='center', batch=self.lbls,
            )

        lbl(u'请拖动调整角色的出场顺序', w//2, h-25)

        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2
        self.width, self.height = w, h
        self.update()

        self.sorter = sorter = KOFSorterControl(parent=self, x=20, y=60)
        selectors = []
        for i, c in enumerate(choices):
            selectors.append(
                GirlSelector(c, selectors, parent=sorter)
            )
        sorter.init()

        btn = Button(parent=self, caption=u'调整完成', x=w-120, y=15, width=100, height=30)

        @btn.event
        def on_click(*a, **k):
            gslist, = self.sorter.get_result()
            index = [c.choice._choice_index for c in gslist]
            ilet.set_result(index)
            ilet.done()
            end_transaction(self.trans)

        b = BigProgressBar(parent=self, x=100, y=15, width=250)
        b.value = LinearInterp(1.0, 0.0, ilet.timeout, on_done=on_click)

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()


mapping = {
    'Action': UIDoPassiveAction,
    'ActionStageAction': UIDoActionStage,
    'ChooseGirl': UIChooseGirl,
    'ChoosePeerCard': UIChoosePeerCard,
    'ChooseOption': UIChooseOption,
    'ChooseIndividualCard': UIChooseIndividualCard,
    'HarvestChoose': UIHarvestChoose,
    'Prophet': UIRanProphet,
    'KOFSort': UIKOFCharacterSorter,
}


input_handler_mapping = {}  # InputTransaction -> UIControl instance


def end_transaction(trans):
    ui = input_handler_mapping.pop(trans, None)
    ui and ui.cleanup()
    ui and ui.delete()


def handle_event(self, _type, arg):
    g = Game.getgame()
    if _type == 'user_input_transaction_begin':
        trans = arg
        log.debug('Processing user_input_transaction_begin: %s', trans)
        if g.me not in trans.involved:
            return

        last = input_handler_mapping.pop(trans, None)
        last and log.error('WTF?! InputTransaction reentrancy')
        last and last.cleanup()

        cls = mapping.get(trans.name, None)
        if not cls:
            log.error('No appropriate input handler for %s !' % trans.name)
            end_transaction(trans)
            return

        this = cls(trans, parent=self)
        input_handler_mapping[trans] = this
        log.debug('End processing user_input_transaction_begin')

    elif _type == 'user_input_transaction_end':
        log.debug('Processing user_input_transaction_end: %s', arg)
        end_transaction(arg)
        log.debug('End processing user_input_transaction_end')

    elif _type == 'user_input':
        from .effects import input_snd_prompt
        input_snd_prompt()

        trans, ilet = arg
        log.debug('Processing user_input: %s', trans)
        ui = input_handler_mapping.get(trans, None)
        if not ui:
            log.error('WTF: no associated transaction')
            log.error('trans: %r  ilet: %r', trans, ilet)
            log.error('hybrid_stack: %r', g.hybrid_stack)
            log.debug('Error processing user_input: %s', trans)
            return

        def afk_autocomplete(*a):
            self.afk and done()

        def done():
            pyglet.clock.unschedule(afk_autocomplete)
            ilet.event.set()
            log.debug('End processing user_input: %s', trans)

        ilet.done = done
        pyglet.clock.schedule_once(afk_autocomplete, 2)
        ui.process_user_input(ilet)
        log.debug('Processing user_input: %s scheduled', trans)

    elif _type == 'user_input_start':
        trans, ilet = arg
        ilet.actor is g.me and self.update_skillbox()
        ui = input_handler_mapping.get(trans, None)
        if not ui: return
        ui.process_user_input_start(ilet)

    elif _type == 'user_input_finish':
        trans, ilet, rst = arg
        ilet.actor is g.me and self.update_skillbox()
        ui = input_handler_mapping.get(trans, None)
        if not ui: return
        ui.process_user_input_finish(ilet, rst)

    elif _type == 'user_input_transaction_feedback':
        trans, evt_name, v = arg
        ui = input_handler_mapping.get(trans, None)
        if not ui: return
        getattr(ui, 'on_' + evt_name)(v)
