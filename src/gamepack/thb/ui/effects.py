# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict as ddict
from functools import partial
import logging

# -- third party --
from pyglet.sprite import Sprite
from pyglet.text import Label
import pyglet

# -- own --
from ..actions import Action, ActionStage, BaseFatetell, Damage, Fatetell, LaunchCard, Pindian
from ..actions import PlayerDeath, PlayerTurn, UserAction
from ..cards import RejectHandler, VirtualCard
from ..inputlets import ActionInputlet
from .game_controls import CardSprite
from client.ui.base.interp import LinearInterp
from client.ui.controls import BalloonPrompt, Button, Colors, Control, Panel, SmallProgressBar
from client.ui.resloader import L
from client.ui.soundmgr import SoundManager
from game.autoenv import Game
from utils import BatchList, group_by

# -- code --
log = logging.getLogger('THBattleUI_Effects')


class OneShotAnim(Sprite):
    def on_animation_end(self):
        self.delete()


class LoopingAnim(Sprite):
    def __init__(self, *a, **k):
        Sprite.__init__(self, *a, **k)
        try:
            self.batch.animations.append(self)
        except:
            pass

    def delete(self):
        try:
            self.batch.animations.remove(self)
        except:
            pass
        Sprite.delete(self)


class TagAnim(Control):
    def __init__(self, img, x, y, text, *a, **k):
        Control.__init__(self, x=x, y=y, width=25, height=25, *a, **k)
        self.image = img
        self.sprite = LoopingAnim(img)
        balloon = BalloonPrompt(self)
        balloon.set_balloon(text)

    def draw(self):
        self.sprite.draw()

    def delete(self):
        Control.delete(self)
        self.sprite.delete()

    def set_position(self, x, y):
        self.x, self.y = x, y


def before_launch_card_effects(self, arg):
    from .. import actions
    act = arg[0]
    rawcards = VirtualCard.unwrap([act.card])
    for cards in group_by(rawcards, lambda c: id(c.resides_in)):
        card_migration_effects(
            self, (
                actions.DropUsedCard(act.source, [act.card]),
                cards,
                cards[0].resides_in,
                self.game.deck.droppedcards,
            )
        )


def card_migration_effects(self, args):  # here self is the SimpleGameUI instance
    act, cards, _from, to = args
    g = self.game
    handcard_update = False
    dropcard_update = False
    csl = BatchList()

    from .. import actions

    # --- src ---
    rawcards = [c for c in cards if not c.is_card(VirtualCard)]

    if _from.type == 'equips':  # equip area
        port = self.player2portrait(_from.owner)
        port.remove_equip_sprites(cards)

    if to is None: return  # not supposed to have visual effects

    hca_mapping = {cs.associated_card: (cs, i) for i, cs in enumerate(self.handcard_area.control_list)}
    dca_mapping = {cs.associated_card: (cs, i+100) for i, cs in enumerate(self.dropcard_area.control_list)}
    pca = None
    for c in rawcards:
        # handcard
        k = hca_mapping.get(c, None)
        if k:
            cs, i = k
            handcard_update = True
            cs.sort_idx = i
            csl.append(cs)
            continue

        # dropped card
        k = dca_mapping.get(c, None)
        if k:
            cs, i = k
            dropcard_update = True
            cs.sort_idx = i
            csl.append(cs)
            continue

        # others
        if not pca:
            if _from.type in ('deckcard', 'droppedcard', 'disputed') or not _from.owner:
                pca = self.deck_area
            # elif not _from.owner:
            #     break
            else:
                pca = self.player2portrait(_from.owner).portcard_area

        cs = CardSprite(c, parent=pca)
        cs.associated_card = c
        cs.sort_idx = -1
        csl.append(cs)

    csl.sort(key=lambda cs: cs.sort_idx)
    csl.update()

    pca and pca.arrange()

    # --- dest ---

    if to.type == 'equips':  # equip area
        port = self.player2portrait(to.owner)
        port.add_equip_sprites(cards)

    if to.owner is g.me and to.type in ('cards', 'showncards'):
        handcard_update = True
        hca = self.handcard_area
        for cs in csl:
            cs.migrate_to(hca)
            cs.gray = False

    else:
        if to.type in ('droppedcard', 'disputed'):
            dropcard_update = True
            ca = self.dropcard_area
            if isinstance(act, BaseFatetell):
                if _from.type != 'disputed':
                    # do not trigger anim twice

                    assert len(csl) == 1
                    csl[0].gray = not act.succeeded  # may be race condition
                    csl[0].do_fatetell_anim()
            else:
                gray = not isinstance(act, (
                    actions.DropUsedCard,
                )) and not to.type == 'disputed'
                for cs in csl:
                    cs.gray = gray
            csl.migrate_to(ca)
        elif to.owner:
            ca = self.player2portrait(to.owner).portcard_area
            for cs in csl:
                cs.migrate_to(ca)
                cs.gray = False
            ca.update()
            ca.fade()
        else:
            for cs in csl:
                cs.delete()

    handcard_update and self.handcard_area.update()
    dropcard_update and self.dropcard_area.update()

    if _from.type == 'fatetell':
        port = self.player2portrait(_from.owner)
        update_tags(self, _from.owner)

    if to.type == 'fatetell':
        port = self.player2portrait(to.owner)
        update_tags(self, to.owner)


def damage_effect(self, act):
    t = act.target
    port = self.player2portrait(t)
    OneShotAnim(L('thb-hurt'), x=port.x, y=port.y, batch=self.animations)


def update_tags(self, p):
    port = self.player2portrait(p)
    taganims = port.taganims

    for t in taganims:
        t.delete()

    taganims[:] = []

    from .ui_meta.tags import tags as tags_meta

    # --- fatetell card
    ftcl = getattr(p, 'fatetell', ())
    for c in ftcl:
        a = TagAnim(
            L(c.ui_meta.tag_anim(c)),
            0, 0,
            c.ui_meta.description,
            parent=self,
        )
        taganims.append(a)

    for t in list(p.tags):
        meta = tags_meta.get(t)
        if meta and meta.display(p, p.tags[t]):
            a = TagAnim(
                L(tags_meta[t].tag_anim(p)),
                0, 0,
                tags_meta[t].description,
                parent=self,
            )
            taganims.append(a)

    port.tagarrange()


def after_launch_effect(self, act):
    update_tags(self, act.source)
    for p in act.target_list:
        update_tags(self, p)


def action_stage_effect_before(self, act):
    update_tags(self, act.target)

action_stage_effect_after = action_stage_effect_before


def player_turn_effect(self, act):
    p = act.target
    port = self.player2portrait(p)
    if not hasattr(self, 'turn_frame') or not self.turn_frame:
        self.turn_frame = LoopingAnim(
            L('c-turn_frame'),
            batch=self.animations
        )
    self.turn_frame.position = (port.x - 6, port.y - 4)
    self.prompt_raw('--------------------\n')
    for _p in Game.getgame().players:
        update_tags(self, _p)


def player_death_update(self, act):
    self.player2portrait(act.target).update()
    update_tags(self, act.target)


def player_turn_after_update(self, act):
    global input_snd_enabled
    player_death_update(self, act)
    if act.target is Game.getgame().me:
        input_snd_enabled = True


def _aese(_type, self, act):
    meta = getattr(act, 'ui_meta', None)
    if not meta: return
    prompt = getattr(meta, _type, None)
    if not prompt: return
    s = prompt(act)
    if s is not None:
        if isinstance(s, (tuple, list)):
            [self.prompt(i) for i in s]
        else:
            self.prompt(s)


action_effect_string_before = partial(_aese, 'effect_string_before')
action_effect_string_after = partial(_aese, 'effect_string')
action_effect_string_apply = partial(_aese, 'effect_string_apply')


def action_effect_before(self, act):
    action_effect_string_before(self, act)
    if hasattr(act, 'ui_meta'):
        rays = getattr(act.ui_meta, 'ray', None)
        rays = rays(act) if rays else []
        for f, t in rays:
            self.ray(f, t)


def action_effect_apply(self, act):
    action_effect_string_apply(self, act)
    if hasattr(act, 'ui_meta'):
        se = getattr(act.ui_meta, 'sound_effect', None)
        se = se and se(act)
        se and SoundManager.play(se, 'cv')


def action_effect_after(self, act):
    action_effect_string_after(self, act)
    if hasattr(act, 'ui_meta'):
        se = getattr(act.ui_meta, 'sound_effect_after', None)
        se = se and se(act)
        se and SoundManager.play(se, 'cv')


class UIPindianEffect(Panel):
    def __init__(self, act, *a, **k):
        w = 20 + 91 + 20 + 91 + 20
        h = 20 + 125 + 20 + 20 + 20

        self.action = act
        src = act.source
        tgt = act.target

        self.lbls = batch = pyglet.graphics.Batch()

        self.srclbl = Label(
            text=src.ui_meta.char_name, x=20+91//2, y=165, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
            anchor_x='center', anchor_y='bottom', batch=batch
        )

        self.tgtlbl = Label(
            text=tgt.ui_meta.char_name, x=20+91+20+91//2, y=165, font_size=12,
            color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
            anchor_x='center', anchor_y='bottom', batch=batch
        )

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)
        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2 + 20
        self.width, self.height = w, h
        self.update()

        parent.game_event += self.on_game_event

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()

    def on_game_event(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, Pindian):
            rst = arg.succeeded
            if rst:
                self.tgtcs.gray = True
                self.srclbl.color = (80, 255, 80, 255)
                self.tgtlbl.color = (0, 0, 0, 0)
            else:
                self.srccs.gray = True
                self.tgtlbl.color = (80, 255, 80, 255)
                self.srclbl.color = (0, 0, 0, 0)

            self.srccs.update()
            self.tgtcs.update()

            pyglet.clock.schedule_once(lambda *a: self.delete(), 2)

        elif evt_type == 'pindian_card_revealed':
            self.srccs.update()
            self.tgtcs.update()

        elif evt_type == 'pindian_card_chosen':
            p, card = arg
            if p is self.action.source:
                self.srccs = CardSprite(card, parent=self, x=20, y=20)
            else:
                self.tgtcs = CardSprite(card, parent=self, x=20+91+20, y=20)

            from .. import actions
            card_migration_effects(
                self.parent, (
                    actions.DropUsedCard(p, [card]),
                    [card],
                    card.resides_in,
                    self.parent.game.deck.droppedcards,
                )
            )

    def delete(self):
        if self.parent:
            self.parent.game_event -= self.on_game_event

        Panel.delete(self)


def pindian_effect(self, act):
    UIPindianEffect(act, parent=self)


def input_snd_prompt():
    SoundManager.play('c-sound-input')


input_snd_enabled = True


def user_input_effects(self, ilet):
    global input_snd_enabled
    import sys
    if sys.platform == 'win32':
        from ctypes import windll
        u = windll.user32
        from client.ui.base.baseclasses import main_window
        if u.GetForegroundWindow() != main_window._hwnd:
            u.FlashWindow(main_window._hwnd, 1)

    g = Game.getgame()
    if getattr(g, 'current_turn', None) is not g.me:
        input_snd_enabled = True

    # HACK
    if input_snd_enabled:
        if isinstance(ilet, ActionInputlet) and isinstance(ilet.initiator, RejectHandler):
            input_snd_prompt()

    if getattr(g, 'current_turn', None) is g.me:
        input_snd_enabled = False


mapping_actions = ddict(dict, {
    'before': {
        Pindian:     pindian_effect,
        ActionStage: action_stage_effect_before,
        PlayerTurn:  player_turn_effect,
        Action:      action_effect_before,
    },
    'apply': {
        Action: action_effect_apply,
        Damage: damage_effect,
    },
    'after': {
        PlayerDeath: player_death_update,
        LaunchCard:  after_launch_effect,
        ActionStage: action_stage_effect_after,
        PlayerTurn:  player_turn_after_update,
        Action:      action_effect_after,
    }
})


def action_effects(_type, self, act):
    cls = act.__class__

    if isinstance(act, UserAction):
        g = self.game
        for p in g.players:
            update_tags(self, p)

    while cls is not object:
        f = mapping_actions[_type].get(cls)
        f and f(self, act)
        cls = cls.__base__


def user_input_start_effects(self, arg):
    trans, ilet = arg
    cturn = getattr(self, 'current_turn', None)

    if trans.name == 'ActionStageAction':
        self.dropcard_area.fade()

    p = ilet.actor
    port = self.player2portrait(p)
    if p is not cturn:
        # drawing turn frame
        port.actor_frame = LoopingAnim(
            L('c-actor_frame'),
            x=port.x - 6, y=port.y - 4,
            batch=self.animations
        )

    pbar = SmallProgressBar(
        parent=self,
        x=port.x, y=port.y - 15,
        width=port.width,
        # all animations have zindex 2,
        # turn/target frame will overdrawn on this
        # if zindex<2
        zindex=3,
    )

    pbar.value = LinearInterp(
        1.0, 0.0, ilet.timeout,
        on_done=lambda self, desc: self.delete(),
    )
    port.actor_pbar = pbar


def user_input_finish_effects(self, arg):
    trans, ilet, rst = arg
    p = ilet.actor

    port = self.player2portrait(p)
    if getattr(port, 'actor_frame', False):
        port.actor_frame.delete()
        port.actor_frame = None

    if getattr(port, 'actor_pbar', False):
        port.actor_pbar.delete()
        port.actor_pbar = None


def game_roll_prompt(self, pl):
    self.prompt(u'Roll点顺序：')
    for p in pl:
        self.prompt(p.account.username)
    self.prompt_raw('--------------------\n')


def game_roll_result_prompt(self, p):
    self.prompt(u'|R%s|r点数最大' % p.account.username)


def reseat_effects(self, _):
    pl = self.game.players.rotate_to(self.game.me)
    ports = [self.player2portrait(p) for p in pl]
    assert set(ports) == set(self.char_portraits)
    locations = self.gcp_location[:len(self.game.players)]
    for port, (x, y, tp, _) in zip(ports, locations):
        port.tag_placement = tp
        port.animate_to(x, y)
        port.update()
    self.char_portraits[:] = ports


def mutant_morph_effects(self, mutant):
    meta = mutant.ui_meta
    gs = self.get_game_screen()

    gs.set_flash(5.0)
    gs.set_color(getattr(Colors, meta.color_scheme))
    gs.backdrop = L(meta.wallpaper)
    SoundManager.instant_switch_bgm(meta.bgm)


class UIShowCardsEffect(Panel):
    def __init__(self, target, cards, *a, **k):
        Panel.__init__(
            self, x=1, y=1, width=1, height=1, zindex=5,
            *a, **k
        )
        self.lbls = lbls = pyglet.graphics.Batch()

        w, h = 95 * len(cards), 125
        w = 30 + w + 30
        h = 60 + h + 50

        def lbl(text, x, y):
            Label(
                text=text, x=x, y=y, font_size=12,
                anchor_x='center', anchor_y='center',
                color=(255, 255, 160, 255), shadow=(2, 0, 0, 0, 230),
                batch=lbls,
            )

        lbl(u'%s展示的牌' % target.ui_meta.char_name, w//2, h-25)

        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2
        self.width, self.height = w, h
        self.update()

        for i, c in enumerate(cards):
            cs = CardSprite(c, parent=self, x=30 + 95 * i, y=60)
            cs.associated_card = c

        btn = Button(parent=self, caption=u'看完了', x=w-122, y=15, width=100, height=30)

        @btn.event
        def on_click(*a):
            self.delete()

        pyglet.clock.schedule_once(lambda _: self.delete(), 0.5 + len(cards) * 1.2)

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()


def showcards_effect(self, arg):
    target, cards = arg
    UIShowCardsEffect(target, cards, parent=self)


def fatetell_effect(self, act):
    self.prompt(Fatetell.ui_meta.fatetell_prompt_string(act))


mapping_events = ddict(bool, {
    'action_before':     partial(action_effects, 'before'),
    'action_apply':      partial(action_effects, 'apply'),
    'action_after':      partial(action_effects, 'after'),
    'fatetell':          fatetell_effect,
    'user_input_start':  user_input_start_effects,
    'user_input':        user_input_effects,
    'user_input_finish': user_input_finish_effects,
    'card_migration':    card_migration_effects,
    'choose_target':     before_launch_card_effects,
    'game_roll':         game_roll_prompt,
    'game_roll_result':  game_roll_result_prompt,
    'reseat':            reseat_effects,
    'mutant_morph':      mutant_morph_effects,
    'showcards':         showcards_effect,
})


def handle_event(self, _type, data):
    f = mapping_events.get(_type)
    if f: f(self, data)
