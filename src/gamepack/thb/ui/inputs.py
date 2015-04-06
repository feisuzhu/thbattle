# -*- coding: utf-8 -*-

# -- stdlib --
import logging
import math

# -- third party --
from gevent.event import Event
from pyglet.gl import glColor3f, glColor4f, glRectf
from pyglet.text import Label
import gevent
import pyglet

# -- own --
from .game_controls import CardSelectionPanel, CardSprite, DropCardArea
from client.ui.base.interp import AbstractInterp, InterpDesc, LinearInterp, SineInterp, getinterp
from client.ui.controls import BigProgressBar, Button, ConfirmButtons, Control, ImageButton
from client.ui.controls import ImageSelector, Panel, SmallProgressBar, TextArea
from client.ui.resloader import L
from client.ui.soundmgr import SoundManager
from game.autoenv import Game
from gamepack.thb import actions as thbactions
from gamepack.thb.cards import Card, CardList, RejectCard


# -- code --
log = logging.getLogger('THBattleUI_Input')


class InputHandler(object):
    def process_user_input_start(self, ilet):
        pass

    def process_user_input(self, ilet):
        pass

    def process_user_input_finish(self, ilet, rst):
        pass

    def delete(self):
        pass

    def cleanup(self):
        pass


class UIActionConfirmButtons(ConfirmButtons):
    DEFAULT_BUTTONS = ((u'确定', True), (u'结束', False))

    def __init__(self, buttons=DEFAULT_BUTTONS, delay=0.5, **k):
        self._valid = True
        k.setdefault('min_width', 80 if len(buttons) <= 2 else 20)
        ConfirmButtons.__init__(self, buttons=buttons, delay=delay, **k)

    def update(self):
        for b in self.buttons:
            b.state = Button.DISABLED if self.disabled else Button.NORMAL

        if not self.valid:
            self.buttons[0].state = Button.DISABLED

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, valid):
        self._valid = valid
        self.update()

    def disable(self):
        self.disabled = True
        self.update()

    def enable(self):
        self.disabled = False
        self.update()


class UISelectTarget(Control, InputHandler):

    def __init__(self, trans, *a, **k):
        Control.__init__(self, zindex=15, *a, **k)
        self.trans = trans
        self.inputlet = None
        self.label = None
        self.action_params = {}
        self.view = self.parent
        self.x, self.y, self.width, self.height = (285, 162, 531, 58)

    def process_user_input(self, ilet):
        view = self.view
        self.inputlet = ilet

        self.confirmbtn = UIActionConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
        )
        self.progress_bar = BigProgressBar(parent=self, x=0, y=0, width=250)
        self.label = Label(
            text=u"HEY SOMETHING'S WRONG", x=125, y=28, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 179),
            anchor_x='center', anchor_y='bottom',
        )

        view.selection_change += self._on_selection_change

        g = Game.getgame()
        port = view.player2portrait(g.me)
        port.equipcard_area.clear_selection()

        # view.selection_change.notify()  # the clear_selection thing will trigger this

        @self.confirmbtn.event
        def on_confirm(is_ok, force=False):
            if is_ok:
                ilet.set_result(*self.get_result())

            elif not force and view.get_selected_skills():
                view.reset_selected_skills()
                return

            ilet.done()
            end_transaction(self.trans)

        self.progress_bar.value = LinearInterp(
            1.0, 0.0, ilet.timeout,
            on_done=lambda *a: on_confirm(False, force=True)
        )

    def set_text(self, text):
        self.label.text = text

    def _on_selection_change(self):
        self.set_valid(False)
        self.on_selection_change()

    def on_selection_change(self):
        # subclasses should surpress it
        self.set_valid()

    def get_result(self):  # override this to customize
        view = self.view
        return [
            view.get_selected_skills(),
            view.get_selected_cards(),
            view.get_selected_players(),
            view.get_action_params(),
        ]

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def cleanup(self):
        if not self.label: return  # processed user_input
        self.view.end_select_player()

    def set_valid(self, valid=True):
        self.confirmbtn.valid = valid

    def draw(self):
        self.draw_subcontrols()
        lbl = self.label
        lbl and lbl.draw()

    def delete(self):
        self.view.selection_change -= self._on_selection_change
        super(UISelectTarget, self).delete()


class UIDoPassiveAction(UISelectTarget):
    _auto_chosen = False

    def on_selection_change(self):
        ilet = self.inputlet
        if not ilet: return

        view = self.parent
        if not view: return

        if ilet.categories and not self._auto_chosen:
            self._auto_chosen = True
            c = ilet.ui_meta.passive_action_recommend(ilet)
            if c:
                hca = view.handcard_area
                for cs in hca.cards:
                    if cs.associated_card == c:
                        hca.toggle(cs, 0.3)
                        return

        view = self.parent
        skills = view.get_selected_skills()
        rawcards = view.get_selected_cards()
        params = view.get_action_params()
        players = view.get_selected_players()
        ilet = self.inputlet

        rst = ilet.ui_meta.passive_action_disp(ilet, skills, rawcards, params, players)

        rst.valid and self.set_valid()
        self.set_text(rst.prompt)
        if rst.pl_selecting:
            view.begin_select_player(rst.pl_disabled)
            view.set_selected_players(rst.pl_selected)
        else:
            view.end_select_player()

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


class UIDoRejectCardResponse(UIDoPassiveAction):
    _auto_chosen = False

    def process_user_input(self, ilet):
        # Override
        view = self.view
        buttons = ((u'确定', 'fire'), (u'结束', 'cancel'))
        target_act = ilet.initiator.target_act
        pact = thbactions.ForEach.get_actual_action(target_act)

        g = Game.getgame()

        if pact:
            if g.me.tags['__reject_dontcare'] is pact:
                ilet.done()
                end_transaction(self.trans)
                return

            buttons = ((u'确定', 'fire'), (u'结束', 'cancel'), (u'此次不再使用', 'dontcare'))

        self.confirmbtn = UIActionConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24, buttons=buttons,
        )

        self.progress_bar = BigProgressBar(parent=self, x=0, y=0, width=250)
        self.label = Label(
            text=u"HEY SOMETHING'S WRONG", x=125, y=28, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 179),
            anchor_x='center', anchor_y='bottom',
        )

        view.selection_change += self._on_selection_change

        port = view.player2portrait(g.me)
        port.equipcard_area.clear_selection()

        # view.notify.selection_change.notify() # the clear_selection thing will trigger this

        @self.confirmbtn.event
        def on_confirm(v, force=False):
            if v == 'fire':
                ilet.set_result(*self.get_result())

            elif v == 'cancel' and not force and view.get_selected_skills():
                view.reset_selected_skills()
                return

            elif v == 'dontcare':
                g.me.tags['__reject_dontcare'] = pact

            ilet.done()
            end_transaction(self.trans)

        self.progress_bar.value = LinearInterp(
            1.0, 0.0, ilet.timeout,
            on_done=lambda *a: on_confirm('cancel', force=True)
        )

        self.inputlet = ilet
        assert not ilet.candidates

        self.set_valid_waiter = ev = Event()
        g = Game.getgame()
        gevent.spawn_later(0.1 + 0.2 * math.sqrt(g.players.index(g.me)), ev.set)

        self.set_text(u'自动结算好人卡…')
        if not RejectCard.ui_meta.has_reject_card(g.me):
            ilet.done()
            end_transaction(self.trans)

        self.view.selection_change.notify()

    def set_valid(self, v=True):
        if v:
            @gevent.spawn
            def sv():
                self.set_valid_waiter.wait()
                UIDoPassiveAction.set_valid(self)
        else:
            UIDoPassiveAction.set_valid(self, False)

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
    def on_selection_change(self):
        ilet = self.inputlet
        if not ilet: return

        view = self.parent
        if not view: return

        skills = view.get_selected_skills()
        rawcards = view.get_selected_cards()
        params = view.get_action_params()
        players = view.get_selected_players()

        rst = ilet.ui_meta.active_action_disp(ilet, skills, rawcards, params, players)

        rst.valid and self.set_valid()
        self.set_text(rst.prompt)
        if rst.pl_selecting:
            view.begin_select_player(rst.pl_disabled)
            view.set_selected_players(rst.pl_selected)
        else:
            view.end_select_player()


class GirlSelector(ImageSelector):
    x = InterpDesc('_x')
    y = InterpDesc('_y')

    def __init__(self, choice, group, x=0, y=0, *a, **k):

        self.choice = choice
        cc = choice.char_cls
        meta = cc.ui_meta
        pimg = L(meta.port_image)
        self.char_name = meta.char_name
        self.char_maxlife = cc.maxlife

        self.x = x
        self.y = y
        ImageSelector.__init__(
            self, pimg, group, *a, **k
        )

        self.balloon.set_balloon(meta.description)


class UIBaseChooseGirl(Panel, InputHandler):
    hover_pic = None

    def __init__(self, trans, *a, **k):
        self.trans = trans
        self.pbar = None
        self.selecting = False

        g = Game.getgame()
        choices = trans.mapping[g.me]
        n_choices = len(choices)

        cols = 5 if n_choices > 16 else 4
        rows = max((n_choices - 1) / cols + 1, 4)

        w, h = 20 + cols*160, 51 + rows*113 + 30
        Panel.__init__(self, width=w, height=h, zindex=5, *a, **k)
        p = self.parent
        pw, ph = p.width, p.height
        self.x, self.y = (pw - w)/2, (ph - h)/2
        self.inputlet = None
        choices = self.choices = [c for c in choices if c.char_cls and not getattr(c, 'chosen', False)]
        self.selectors = selectors = []
        for i, c in enumerate(choices):
            y, x = divmod(i, cols)
            x, y = 15 + 160*x, 45 + 113*(rows - 1 - y)
            gs = GirlSelector(c, selectors, parent=self, hover_pic=self.hover_pic, x=x, y=y)

            @gs.event
            def on_dblclick(gs=gs):
                c = gs.choice
                ilet = self.inputlet
                if not c.chosen and ilet:
                    ilet.set_choice(c)
                    ilet.done()
                    self.end_selection()

            selectors.append(gs)

        self.label = Label(
            text='等待其他玩家操作', x=w//2, y=51+rows*113, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
            anchor_x='center', anchor_y='bottom'
        )

    def draw(self):
        Panel.draw(self)
        self.label.draw()

    def on_girl_chosen(self, arg):
        actor, choice = arg
        for c in self.selectors:
            if c.choice is choice:
                c.disable()
                break

        self.parent.update_portraits()

    def begin_selection(self):
        self.selecting = True
        self.pbar and self.pbar.delete()
        self.pbar = BigProgressBar(
            parent=self, x=(self.width-250)//2, y=9, width=250,
        )

        def on_done(*a):
            # self.inputlet.done()
            # FIXME: blindly did this.
            self.inputlet and self.inputlet.done()
            self.end_selection()

        self.pbar.value = LinearInterp(
            1.0, 0.0, self.inputlet.timeout,
            on_done=on_done,
        )

    def end_selection(self):
        self.inputlet = None
        self.selecting = False
        self.pbar.delete()


class UIChooseGirl(UIBaseChooseGirl):
    hover_pic = None

    def process_user_input_start(self, ilet):
        self.label.color = (255, 255, 160, 255)
        self.label.text = u'等待%s选择角色' % (ilet.actor.account.username)
        self.parent.prompt(u'|R%s|r正在选择……' % ilet.actor.account.username)

    def process_user_input(self, ilet):
        assert ilet.actor is Game.getgame().me
        self.inputlet = ilet
        self.label.text = u'请你选择一名角色'
        self.label.color = (160, 251, 255, 255)
        self.begin_selection()

    def process_user_input_finish(self, ilet, rst):
        if not self.selecting:
            self.label.text = u'等待其他玩家操作'
            self.label.color = (255, 255, 160, 255)
            self.inputlet = None

    def on_girl_chosen(self, arg):
        UIBaseChooseGirl.on_girl_chosen(self, arg)
        actor, choice = arg
        choice and choice.char_cls and self.parent.prompt(u'|R%s|r选择了|G【%s】|r' % (
            actor.account.username,
            choice.char_cls.ui_meta.char_name,
        ))


class UIBanGirl(UIBaseChooseGirl):
    hover_pic = L('c-imagesel_ban')

    def process_user_input_start(self, ilet):
        self.label.color = (255, 255, 160, 255)
        self.label.text = u'等待%s选择不能出场的角色' % (ilet.actor.account.username)
        self.parent.prompt(u'|R%s|r正在BAN……' % ilet.actor.account.username)

    def process_user_input(self, ilet):
        assert ilet.actor is Game.getgame().me
        self.inputlet = ilet
        self.label.text = u'请你选择不能出场的角色'
        self.label.color = (160, 251, 255, 255)
        self.begin_selection()

    def process_user_input_finish(self, ilet, rst):
        self.label.text = u'等待其他玩家操作'
        self.label.color = (255, 255, 160, 255)
        self.inputlet = None

    def on_girl_chosen(self, arg):
        UIBaseChooseGirl.on_girl_chosen(self, arg)
        actor, choice = arg
        choice and choice.char_cls and self.parent.prompt(u'|R%s|rBAN掉了|G【%s】|r' % (
            actor.account.username,
            choice.char_cls.ui_meta.char_name,
        ))


class UIChoosePeerCard(CardSelectionPanel, InputHandler):
    def __init__(self, trans, *a, **k):
        self.trans = trans
        self.lbls = pyglet.graphics.Batch()
        CardSelectionPanel.__init__(self, zindex=5, *a, **k)

    def process_user_input(self, ilet):
        self.ilet = ilet
        target = ilet.target

        card_lists = [
            (CardList.ui_meta.lookup[cat], getattr(target, cat))
            for cat in ilet.categories
        ]

        self.init(card_lists)

        self.progress_bar = b = BigProgressBar(
            parent=self, x=(self.width-250)//2, y=7, width=250
        )
        b.value = LinearInterp(
            1.0, 0.0, ilet.timeout,
            on_done=lambda *a: self.cleanup()
        )

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()

    def delete(self):
        try:
            self.ilet.done()
        except AttributeError:
            pass

        super(UIChoosePeerCard, self).delete()

    def on_confirm(self, cs):
        ilet = self.ilet
        ilet.set_card(cs.associated_card)
        ilet.done()
        end_transaction(self.trans)


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

        self.confirmbtn = UIActionConfirmButtons(
            parent=self, x=259, y=4, width=165, height=24,
            buttons=choose_option_buttons,
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
            L('c-buttons-close_blue'),
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
            text=u"等待其他玩家操作", x=w//2, y=300, font_size=12,
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
        self.lbl.text = u'等待其他玩家操作'
        self.lbl.color = (255, 255, 160, 255)
        self.inputlet = None

    def on_harvest_choose(self, card):
        self.mapping[id(card)].gray = True


class Dragger(Control):
    dragging = False

    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.width, self.height = self.expected_size(self.rows, self.cols)

    @classmethod
    def expected_size(cls, rows=None, cols=None):
        return (
            (cls.item_width + 4) * (cols or cls.cols),
            (cls.item_height + 15) * (rows or cls.rows),
        )

    def update(self):
        for j, l in enumerate(reversed(self.sprites)):
            for i, cs in enumerate(l):
                nx, ny = self._to_loc(i, j)
                cs.x = SineInterp(cs.x, nx, 0.3)
                cs.y = SineInterp(cs.y, ny, 0.3)
                self.update_sprite(cs, i, j)

        self.dispatch_event('on_update')

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

Dragger.register_event_type('on_update')


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


class CharacterSorterControl(Dragger):
    rows = 1
    item_width, item_height = 145, 96

    def __init__(self, total, limit, *a, **k):
        Dragger.__init__(self, *a, cols=total, **k)
        self.limit = limit

    def update_sprite(self, c, i, j):
        c.disable() if i >= self.limit else c.enable()


class UICharacterSorter(Panel, InputHandler):
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

        w, h = CharacterSorterControl.expected_size(1, ilet.num)
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

        self.sorter = sorter = CharacterSorterControl(
            ilet.num, ilet.limit,
            parent=self, x=20, y=60
        )
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


class KokoroHopeMaskControl(Dragger):
    cols, rows = 4, 2
    item_width, item_height = 91, 125


class UIKokoroHomeMask(Panel, InputHandler):
    def __init__(self, trans, parent, *a, **k):
        Panel.__init__(
            self, x=1, y=1, width=1, height=1, zindex=5, parent=parent,
            *a, **k
        )
        self.lbls = pyglet.graphics.Batch()
        self.trans = trans

    def process_user_input(self, ilet):
        cards = ilet.cards

        w, h = KokoroHopeMaskControl.expected_size()
        w = 100 + w + 20
        h = 60 + h + 50

        def lbl(text, x, y):
            Label(
                text=text, x=x, y=y, font_size=12,
                anchor_x='center', anchor_y='center',
                color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
                batch=self.lbls,
            )

        lbl(u'请拖动调整牌的位置，获得的牌必须是同花色的', w // 2, h - 25)
        lbl(u'牌堆顶', 50, 277)
        lbl(u'展示并获得', 50, 122)

        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2
        self.width, self.height = w, h
        self.update()

        self.ctrl = ctrl = KokoroHopeMaskControl(parent=self, x=100, y=60)
        for i, c in enumerate(cards):
            cs = CardSprite(c, parent=ctrl)
            cs.associated_card = c

        ctrl.init()

        btn = Button(parent=self, caption=u'完成', x=w-120, y=15, width=100, height=30)

        @btn.event
        def on_click(*a):
            ilet.done()
            end_transaction(self.trans)

        @ctrl.event
        def on_update():
            putback, acquire = self.ctrl.get_result()
            putback = [c.associated_card for c in putback]
            acquire = [c.associated_card for c in acquire]
            if ilet.is_valid(putback, acquire):
                ilet.set_result(putback, acquire)
                btn.state = Button.NORMAL
            else:
                btn.state = Button.DISABLED

        b = BigProgressBar(parent=self, x=100, y=15, width=250)
        b.value = LinearInterp(1.0, 0.0, ilet.timeout, on_done=on_click)

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()


class UIMorphingCardSelection(CardSelectionPanel):
    last_cards = None

    def __init__(self, parent, *a, **k):
        CardSelectionPanel.__init__(self, parent=parent, zindex=10, *a, **k)
        self.view = view = parent
        view.selection_change += self.on_view_selection_change
        self.panel = None
        self.on_view_selection_change()

    def on_view_selection_change(self):
        view = self.view
        cl = view.get_selected_cards()

        if cl == self.last_cards: return
        self.last_cards = cl

        from gamepack.thb.characters.mamizou import Morphing

        cards = Morphing.list_morph_cards(cl)
        card_lists = []

        l = [c for c in cards if 'basic' in c.category]
        l and card_lists.append(('基本牌', l))

        l = [c for c in cards if 'instant_spellcard' in c.category]
        l and card_lists.append(('符卡', l))

        self.selection_mode = CardSelectionPanel.SINGLE
        self.init(card_lists, multiline=len(card_lists) < 2)

    def on_selection_change(self):
        view = self.view
        params = view.get_action_params()
        if self.selection:
            card = self.selection[0].associated_card
            params['mamizou_morphing'] = card.__class__.__name__
        else:
            try:
                del params['mamizou_morphing']
            except:
                pass

        view.selection_change.notify()

    def delete(self):
        if self.panel:
            self.panel.delete()

        self.view.selection_change -= self.on_view_selection_change
        super(UIMorphingCardSelection, self).delete()


class UIDebugUseCardSelection(CardSelectionPanel):
    def __init__(self, parent, *a, **k):
        CardSelectionPanel.__init__(self, parent=parent, zindex=10, *a, **k)
        self.view = view = parent
        view.selection_change += self.on_selection_change
        self.panel = None
        self.on_selection_change()

    def on_selection_change(self):
        view = self.view
        params = view.get_action_params()

        def cancel():
            if self.panel:
                self.panel.delete()
                self.panel = None
                try:
                    del params['debug_card']
                except:
                    pass

        if self.panel:
            return

        cl = [c() for c in Card.card_classes.values()]
        card_lists = [('', cl[i:i+12]) for i in xrange(0, len(cl), 12)]
        self.panel = panel = CardSelectionPanel(
            parent=self.parent, zindex=10,
            selection_mode=CardSelectionPanel.SINGLE,
        )
        panel.init(card_lists, multiline=False)

        @panel.event
        def on_selection_change():
            if panel.selection:
                card = panel.selection[0].associated_card
                params['debug_card'] = card.__class__.__name__
            else:
                try:
                    del params['debug_card']
                except:
                    pass

            self.view.selection_change.notify()

    def delete(self):
        if self.panel:
            self.panel.delete()

        self.view.selection_change -= self.on_selection_change
        CardSelectionPanel.delete(self)


class UIGalgameDialog(Control, InputHandler):

    def __init__(self, trans, parent, *a, **k):
        y, w, h = (162, 531, 100)
        x = (parent.width - w) // 2 + 30
        Control.__init__(self, *a, x=x, y=y, width=w, height=h, zindex=999999, parent=parent, **k)
        self.trans = trans
        self.should_draw = False
        self.lbls = pyglet.graphics.Batch()

    def process_user_input(self, ilet):
        meta = ilet.character.ui_meta
        self.texture = L(meta.port_image)

        Label(
            text=meta.char_name, x=2, y=80, font_size=12,
            anchor_x='left', anchor_y='bottom',
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
            batch=self.lbls,
        )

        ta = TextArea(
            parent=self,
            font_size=9,
            x=0, y=0, width=self.width, height=80 - 2,
        )

        ta.append(ilet.dialog)

        def on_mouse_press(*a, **k):
            ilet.set_result(0)
            ilet.done()
            end_transaction(self.trans)

        self.event(on_mouse_press)
        ta.event(on_mouse_press)

        self.should_draw = True

        if ilet.voice:
            self.player = SoundManager.play(ilet.voice)
        else:
            self.player = None

        b = SmallProgressBar(parent=self, x=self.width - 140, y=0, width=140)
        b.value = LinearInterp(1.0, 0.0, ilet.timeout)

    def draw(self):
        if not self.should_draw: return
        glColor3f(1, 1, 1)
        self.texture.blit(0, 100)
        glColor4f(1, 1, 1, 0.65)
        glRectf(0, 0, self.width, 100)
        self.lbls.draw()
        self.draw_subcontrols()

    def delete(self):
        p = self.player
        if p:
            p.pause()
            self.player = None

        Control.delete(self)


mapping = {
    # InputTransaction name -> Handler class

    'Action':               UIDoPassiveAction,
    'AskForRejectAction':   UIDoRejectCardResponse,
    'Pindian':              UIDoPassiveAction,
    'ActionStageAction':    UIDoActionStage,
    'ChooseGirl':           UIChooseGirl,
    'BanGirl':              UIBanGirl,
    'ChoosePeerCard':       UIChoosePeerCard,
    'ChooseOption':         UIChooseOption,
    'ChooseIndividualCard': UIChooseIndividualCard,
    'GalgameDialog':        UIGalgameDialog,

    'SortCharacter':        UICharacterSorter,

    'HarvestChoose':        UIHarvestChoose,

    'Prophet':              UIRanProphet,
    'HopeMask':             UIKokoroHomeMask,
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
        ilet.actor is g.me and self.refresh_input_state()
        ui = input_handler_mapping.get(trans, None)
        if not ui: return
        ui.process_user_input_start(ilet)

    elif _type == 'user_input_finish':
        trans, ilet, rst = arg
        ilet.actor is g.me and self.refresh_input_state()
        ui = input_handler_mapping.get(trans, None)
        if not ui: return
        ui.process_user_input_finish(ilet, rst)

    elif _type == 'user_input_transaction_feedback':
        trans, evt_name, v = arg
        ui = input_handler_mapping.get(trans, None)
        if not ui: return
        getattr(ui, 'on_' + evt_name)(v)
