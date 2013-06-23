# -*- coding: utf-8 -*-

from client.ui.base.interp import LinearInterp
from client.ui.controls import BalloonPrompt, Colors, Control, Panel, ShadowedLabel, SmallProgressBar
from client.ui.soundmgr import SoundManager

from client.ui.resource import resource as common_res
from resource import resource as gres

from .game_controls import CardSprite, SmallCardSprite

import pyglet

from ..actions import Action, ActionStage, BaseFatetell, Damage, LaunchCard, Pindian, PlayerDeath, PlayerTurn, UserAction
from ..cards import VirtualCard, RejectHandler
from ..inputlets import ActionInputlet

from game.autoenv import Game

from functools import partial
from collections import defaultdict as ddict

from utils import BatchList

from pyglet.sprite import Sprite

import logging
log = logging.getLogger('THBattleUI_Effects')


class OneShotAnim(Sprite):
    def on_animation_end(self):
        self.delete()


LoopingAnim = Sprite


class TagAnim(Control, BalloonPrompt):
    def __init__(self, img, x, y, text, *a, **k):
        Control.__init__(self, x=x, y=y, width=25, height=25, *a, **k)
        self.image = img
        self.sprite = LoopingAnim(img)
        self.init_balloon(text)

    def draw(self):
        self.sprite.draw()

    def set_position(self, x, y):
        self.x, self.y = x, y


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
        equips = self.player2portrait(_from.owner).equipcard_area
        for cs in equips.cards[:]:
            if cs.associated_card in cards:
                cs.delete()
        equips.update()

    if _from.type == 'fatetell':  # fatetell tag
        port = self.player2portrait(_from.owner)
        taganims = port.taganims
        for a in [t for t in taganims if hasattr(t, 'for_fatetell_card')]:
            if a.for_fatetell_card in cards:
                a.delete()
                taganims.remove(a)
        port.tagarrange()

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
            if _from.type in ('deckcard', 'droppedcard') or not _from.owner:
                pca = self.deck_area
            #elif not _from.owner:
            #    break
            else:
                pca = self.player2portrait(_from.owner).portcard_area

        cs = CardSprite(c, parent=pca)
        cs.associated_card = c
        cs.sort_idx = -1
        csl.append(cs)

    csl.sort(key=lambda cs: cs.sort_idx)

    if pca: pca.arrange()

    # --- dest ---

    if to.type == 'equips':  # equip area
        equips = self.player2portrait(to.owner).equipcard_area
        for c in cards:
            cs = SmallCardSprite(c, parent=equips, x=0, y=0)
            cs.associated_card = c
        equips.update()

    if to.type == 'fatetell':  # fatetell tag
        port = self.player2portrait(to.owner)
        taganims = port.taganims
        for c in cards:
            a = TagAnim(
                c.ui_meta.tag_anim(c),
                0, 0,
                c.ui_meta.description,
                parent=self,
            )
            a.for_fatetell_card = c
            port.taganims.append(a)
        port.tagarrange()

    if to.owner is g.me and to.type in ('cards', 'showncards'):
        handcard_update = True
        hca = self.handcard_area
        for cs in csl:
            cs.migrate_to(hca)
            cs.gray = False

    else:
        if to.type == 'droppedcard':
            dropcard_update = True
            ca = self.dropcard_area
            if isinstance(act, BaseFatetell):
                assert len(csl) == 1
                csl[0].gray = not act.succeeded  # may be race condition
                csl[0].do_fatetell_anim()
            else:
                gray = not isinstance(act, (
                    actions.DropUsedCard,
                ))
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

    if handcard_update: self.handcard_area.update()
    if dropcard_update: self.dropcard_area.update()


def damage_effect(self, act):
    t = act.target
    port = self.player2portrait(t)
    OneShotAnim(gres.hurt, x=port.x, y=port.y, batch=self.animations)
    SoundManager.play(gres.sound.hit)


def _update_tags(self, p):
    port = self.player2portrait(p)
    taganims = port.taganims
    old = {a.for_tag: a for a in taganims if hasattr(a, 'for_tag')}
    old_tags = set(old.keys())
    new_tags = set()

    updated_tags = set()

    from .ui_meta import tags as tags_meta

    for t in list(p.tags):
        meta = tags_meta.get(t)
        if meta and meta.display(p, p.tags[t]):
            new_tags.add(t)

    for t in old_tags:  # to be removed
        if t in new_tags:
            anim = tags_meta[t].tag_anim(p)
            if old[t].image == anim:
                continue
            else:
                updated_tags.add(t)
                # fallthrough

        old[t].delete()
        taganims.remove(old[t])

    # for t in new_tags - old_tags: # to be added
    for t in updated_tags | (new_tags - old_tags):  # to be added
        a = TagAnim(
            tags_meta[t].tag_anim(p),
            0, 0,
            tags_meta[t].description,
            parent=self,
        )
        a.for_tag = t
        taganims.append(a)

    port.tagarrange()


def after_launch_effect(self, act):
    _update_tags(self, act.source)
    for p in act.target_list:
        _update_tags(self, p)


def action_stage_effect_before(self, act):
    _update_tags(self, act.target)

action_stage_effect_after = action_stage_effect_before


def player_turn_effect(self, act):
    p = act.target
    port = self.player2portrait(p)
    if not hasattr(self, 'turn_frame') or not self.turn_frame:
        self.turn_frame = LoopingAnim(
            common_res.turn_frame,
            batch=self.animations
        )
    self.turn_frame.position = (port.x - 6, port.y - 4)
    self.prompt_raw('--------------------\n')
    for _p in Game.getgame().players:
        _update_tags(self, _p)


def player_death_update(self, act):
    self.player2portrait(act.target).update()
    _update_tags(self, act.target)


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


class UIPindianEffect(Panel):
    def __init__(self, act, *a, **k):
        w = 20 + 91 + 20 + 91 + 20
        h = 20 + 125 + 20 + 20 + 20

        self.action = act
        src = act.source
        tgt = act.target

        self.lbls = batch = pyglet.graphics.Batch()

        self.srclbl = ShadowedLabel(
            text=src.ui_meta.char_name, x=20+91//2, y=165, font_size=12,
            color=(255, 255, 160, 255), shadow_color=(0, 0, 0, 230),
            anchor_x='center', anchor_y='bottom', batch=batch
        )

        self.tgtlbl = ShadowedLabel(
            text=tgt.ui_meta.char_name, x=20+91+20+91//2, y=165, font_size=12,
            color=(255, 255, 160, 255), shadow_color=(0, 0, 0, 230),
            anchor_x='center', anchor_y='bottom', batch=batch
        )

        Panel.__init__(self, width=1, height=1, zindex=5, *a, **k)
        parent = self.parent
        self.x, self.y = (parent.width - w)//2, (parent.height - h)//2 + 20
        self.width, self.height = w, h
        self.update()

    def draw(self):
        Panel.draw(self)
        self.lbls.draw()

    def on_message(self, _type, *args):
        if _type == 'evt_action_after' and isinstance(args[0], Pindian):
            rst = args[0].succeeded
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

        elif _type == 'evt_pindian_card_chosen':
            p, card = args[0]
            if p is self.action.source:
                self.srccs = CardSprite(card, parent=self, x=20, y=20)
            else:
                self.tgtcs = CardSprite(card, parent=self, x=20+91+20, y=20)


def pindian_effect(self, act):
    UIPindianEffect(act, parent=self)


def input_snd_prompt():
    SoundManager.play(common_res.sound.input)


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
        Pindian: pindian_effect,
        ActionStage: action_stage_effect_before,
        PlayerTurn: player_turn_effect,
        Action: action_effect_before,
    },
    'apply': {
        Action: action_effect_string_apply,
        Damage: damage_effect,
    },
    'after': {
        PlayerDeath: player_death_update,
        LaunchCard: after_launch_effect,
        ActionStage: action_stage_effect_after,
        PlayerTurn: player_turn_after_update,
        Action: action_effect_string_after,
    }
})


def action_effects(_type, self, act):
    cls = act.__class__

    if isinstance(act, UserAction):
        g = self.game
        for p in g.players:
            _update_tags(self, p)

    while cls is not object:
        f = mapping_actions[_type].get(cls)
        if f: f(self, act)
        cls = cls.__base__


def user_input_start_effects(self, arg):
    trans, ilet = arg
    cturn = getattr(self, 'current_turn', None)

    if trans.name == 'ActionStageAction':
        self.dropcard_area.fade()

    if trans.name == 'ChooseGirl':
        self.prompt(u'|R%s|r正在选择……' % ilet.actor.account.username)

    p = ilet.actor
    port = self.player2portrait(p)
    if p is not cturn:
        # drawing turn frame
        port.actor_frame = LoopingAnim(
            common_res.actor_frame,
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
    self.prompt(u'由|R%s|r首先选将、行动' % p.account.username)


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
    gs.backdrop = meta.wallpaper
    SoundManager.instant_switch_bgm(meta.bgm)


mapping_events = ddict(bool, {
    'action_before': partial(action_effects, 'before'),
    'action_apply': partial(action_effects, 'apply'),
    'action_after': partial(action_effects, 'after'),
    'user_input_start': user_input_start_effects,
    'user_input': user_input_effects,
    'user_input_finish': user_input_finish_effects,
    'card_migration': card_migration_effects,
    'game_roll': game_roll_prompt,
    'game_roll_result': game_roll_result_prompt,
    'reseat': reseat_effects,
    'mutant_morph': mutant_morph_effects,
})


def handle_event(self, _type, data):
    f = mapping_events.get(_type)
    if f: f(self, data)
