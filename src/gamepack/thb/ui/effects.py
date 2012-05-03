# -*- coding: utf-8 -*-
from client.ui.base import *
from client.ui.base.interp import *
from client.ui.controls import *

from client.ui import resource as common_res
import resource as gres

from .game_controls import *

import pyglet
from pyglet.gl import *

from ..actions import *
from ..cards import *

from functools import partial
from collections import defaultdict as ddict

from utils import BatchList

import logging
log = logging.getLogger('THBattleUI_Effects')

class OneShotAnim(pyglet.sprite.Sprite):
    def on_animation_end(self):
        self.delete()

LoopingAnim = pyglet.sprite.Sprite

def card_migration_effects(self, args): # here self is the SimpleGameUI instance
    act, cards, _from, to = args
    deck = self.game.deck
    g = self.game
    handcard_update = False
    dropcard_update = False
    csl = BatchList()

    from .. import actions

    # --- src ---
    rawcards = [c for c in cards if not c.is_card(VirtualCard)]

    if _from.type == _from.EQUIPS: # equip area
        equips = self.player2portrait(_from.owner).equipcard_area
        for cs in equips.cards[:]:
            if cs.associated_card in cards:
                cs.delete()
        equips.update()

    if _from.type == _from.FATETELL: # fatetell tag
        port = self.player2portrait(_from.owner)
        taganims = port.taganims
        for a in [t for t in taganims if hasattr(t, 'for_fatetell_card')]:
            if a.for_fatetell_card in cards:
                a.delete()
                taganims.remove(a)
        port.tagarrange()

    if to is None: return # not supposed to have visual effects

    if _from.owner is g.me and _from.type in (_from.HANDCARD, _from.SHOWNCARD):
        handcard_update = True
        csl[:] = [
            cs for cs in self.handcard_area.cards
            if cs.associated_card in cards
        ]

    elif _from.type == _from.DROPPEDCARD:
        dropcard_update = True
        for cs in self.dropcard_area.control_list:
            if cs.associated_card in cards:
                csl.append(cs)

    else:
        if _from.type == _from.DECKCARD:
            pca = self.deck_area
        else:
            try:
                pca = self.player2portrait(_from.owner).portcard_area
            except ValueError:
                raise

        for i, card in enumerate(rawcards):
            cs = CardSprite(card, parent=pca)
            cs.associated_card = card
            csl.append(cs)
        pca.arrange()

    # --- dest ---

    if to.type == to.EQUIPS: # equip area
        equips = self.player2portrait(to.owner).equipcard_area
        for c in cards:
            cs = SmallCardSprite(c, parent=equips, x=0, y=0)
            cs.associated_card = c
        equips.update()

    if to.type == to.FATETELL: # fatetell tag
        port = self.player2portrait(to.owner)
        taganims = port.taganims
        for c in cards:
            a = LoopingAnim(
                c.ui_meta.tag_anim,
                x=0, y=0,
                batch = self.animations
            )
            a.for_fatetell_card = c
            port.taganims.append(a)
        port.tagarrange()

    if to.owner is g.me and to.type in (to.HANDCARD, to.SHOWNCARD):
        handcard_update = True
        hca = self.handcard_area
        for cs in csl:
            cs.migrate_to(hca)
            cs.gray = False

    else:
        if to.type == to.DROPPEDCARD:
            dropcard_update = True
            ca = self.dropcard_area
            if isinstance(act, Fatetell):
                assert len(csl) == 1
                csl[0].gray = not act.succeeded # may be race condition
                csl[0].do_fatetell_anim()
            else:
                gray = not isinstance(act, (
                    actions.DropUsedCard,
                ))
                for cs in csl:
                    cs.gray = gray
            csl.migrate_to(ca)
        else:
            ca = self.player2portrait(to.owner).portcard_area
            for cs in csl:
                cs.migrate_to(ca)
                cs.gray = False
            ca.update()
            ca.fade()

    if handcard_update: self.handcard_area.update()
    if dropcard_update: self.dropcard_area.update()

def damage_effect(self, act):
    t = act.target
    port = self.player2portrait(t)
    #l = t.life
    #port.life = l if l > 0 else 0
    port.update()
    OneShotAnim(common_res.hurt, x=port.x, y=port.y, batch=self.animations)

def heal_effect(self, act):
    t = act.target
    port = self.player2portrait(t)
    #l = t.life
    #port.life = l if l > 0 else 0
    port.update()

def launch_effect(self, act):
    s = act.source
    for t in act.target_list: self.ray(s, t)

def reject_effect(self, act):
    self.ray(act.source, act.target)

def _update_tags(self, p):
    port = self.player2portrait(p)
    taganims = port.taganims
    old = {a.for_tag:a for a in taganims if hasattr(a, 'for_tag')}
    old_tags = set(old.keys())
    new_tags = set()

    from .ui_meta import tags as tags_meta

    for t in p.tags.keys():
        meta = tags_meta.get(t)
        if meta and meta.display(p.tags[t]):
            new_tags.add(t)

    for t in old_tags - new_tags: # to be removed
        old[t].delete()
        taganims.remove(old[t])

    for t in new_tags - old_tags: # to be added
        a = LoopingAnim(
            tags_meta[t].tag_anim,
            x=0, y=0,
            batch = self.animations
        )
        a.for_tag = t
        taganims.append(a)
    port.tagarrange()

def after_launch_effect(self, act):
    _update_tags(self, act.source)
    self.player2portrait(act.source).update()
    for p in act.target_list:
        self.player2portrait(p).update()
        _update_tags(self, p)

def action_stage_update_tag(self, act):
    _update_tags(self, act.actor)

def player_turn_effect(self, act):
    p = act.target
    port = self.player2portrait(p)
    if not hasattr(self, 'turn_frame') or not self.turn_frame:
        self.turn_frame = LoopingAnim(
            common_res.turn_frame,
            batch = self.animations
        )
    self.turn_frame.position = (port.x - 6, port.y - 4)
    self.prompt_raw('--------------------\n')

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

mapping_actions = ddict(dict, {
    'before': {
        LaunchCard: launch_effect,
        Reject: reject_effect,
        ActionStage: action_stage_update_tag,
        PlayerTurn: player_turn_effect,
        Action: action_effect_string_before,
    },
    'apply': {
        Action: action_effect_string_apply,
    },
    'after': {
        DamageEffect: damage_effect,
        Heal: heal_effect,
        LaunchCard: after_launch_effect,
        ActionStage: action_stage_update_tag,
        Action: action_effect_string_after,
    }
})

def action_effects(_type, self, act):
    cls = act.__class__
    while cls is not object:
        f = mapping_actions[_type].get(cls)
        if f:
            f(self, act)
        cls = cls.__base__

def user_input_start_effects(self, input):
    try:
        cturn = self.current_turn
    except AttributeError:
        # game not really started,
        # players are choosing their girl now.
        self.actor_frame = None
        self.actor_pbar = None
        return

    if input.tag == 'action_stage_usecard':
        self.dropcard_area.fade()

    p = input.player
    port = self.player2portrait(p)
    if p is cturn:
        # drawing turn frame
        self.actor_frame = None
    else:
        self.actor_frame = LoopingAnim(
            common_res.actor_frame,
            x=port.x - 6, y=port.y - 4,
            batch = self.animations
        )

    pbar = SmallProgressBar(
        parent = self,
        x = port.x, y = port.y - 15,
        width = port.width,
        # all animations have zindex 2,
        # turn/actor frame will overdrawn on this
        # if zindex<2
        zindex=3,
    )

    pbar.value = LinearInterp(
        1.0, 0.0, input.timeout,
        on_done=lambda self, desc: self.delete(),
    )
    self.actor_pbar = pbar

def user_input_finish_effects(self, input):
    if self.actor_frame:
        self.actor_frame.delete()
        self.actor_frame = None

    if self.actor_pbar:
        self.actor_pbar.delete()
        self.actor_pbar = None

mapping_events = ddict(bool, {
    'action_before': partial(action_effects, 'before'),
    'action_apply': partial(action_effects, 'apply'),
    'action_after': partial(action_effects, 'after'),
    'user_input_start': user_input_start_effects,
    'user_input_finish': user_input_finish_effects,
    'card_migration': card_migration_effects,
})

def handle_event(self, _type, data):
    f = mapping_events.get(_type)
    if f: f(self, data)
