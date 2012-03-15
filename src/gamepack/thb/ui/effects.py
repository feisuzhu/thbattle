# -*- coding: utf-8 -*-
from client.ui.base import *
from client.ui.base.interp import *
from client.ui.controls import *

from client.ui import resource as common_res
import resource as gres

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

def draw_cards_effect(self, act): # here self is the SimpleGameUI instance
    if act.target is self.game.me:
        cards = act.cards
        hca = self.handcard_area
        ax, ay = hca.abs_coords()
        for c in cards:
            cs = CardSprite(
                parent=hca, x=410-ax, y=300-ay,
                img = c.ui_meta.image,
            )
            cs.associated_card = c
        hca.update()
    else: # FIXME: not exactly the effect
        p = self.player2portrait(act.target)
        x, y = p.x + p.width/2, p.y + p.height/2

        n = len(act.cards)
        if n > 1:
            w = 1.5 * CardSprite.width
            step = (w-91)/(n-1)
        else:
            w = CardSprite.width
            step = 0

        def self_destroy(obj, desc):
            obj.delete()

        sy = -CardSprite.height/2
        for i, card in enumerate(act.cards):
            sx = -w*.5 + i*step
            #sy = -CardSprite.height/2
            cs = CardSprite(parent=self)
            cs.x = SineInterp(410+sx, x+sx, 0.3)
            cs.y = SineInterp(300+sy, y+sy, 0.3)
            cs.alpha = ChainInterp(
                FixedInterp(1.0, 0.6),
                CosineInterp(1.0, 0.0, 0.3),
                on_done=self_destroy,
            )
            cs.img = card.ui_meta.image

def drop_cards_effect(gray, self, act):
    if act.target is self.game.me:
        csl = self.handcard_area.cards
        cards = act.cards
        for cs in csl[:]:
            if cs.associated_card in cards:
                cs.migrate_to(self.dropcard_area)
                cs.gray = gray
        self.dropcard_area.update()
        self.handcard_area.update()
    else:
        p = self.player2portrait(act.target)
        x, y = p.x + p.width/2, p.y + p.height/2
        shift = (len(act.cards)+1)*CardSprite.width/2
        for i, card in enumerate(act.cards):
            cs = CardSprite(
                parent=self, x=x-shift+i*CardSprite.width/2,
                y=y-CardSprite.height/2,
                img=card.ui_meta.image,
            )
            cs.gray = gray
            cs.migrate_to(self.dropcard_area)
        self.dropcard_area.update()

drop_cards_gray_effect = partial(drop_cards_effect, True)
drop_cards_normal_effect = partial(drop_cards_effect, False)

def card_migration_effects(self, args):
    act, cards, _from, to = args
    deck = self.game.deck
    g = self.game
    handcard_update = False
    dropcard_update = False
    csl = BatchList()

    from .. import actions

    # --- src ---

    if _from.owner is g.me and _from.type == _from.HANDCARD:
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
                cs.alpha = 1.0 # FIXME: hack: prevent card from fading out

    else:
        if _from.type == _from.DECKCARD:
            pca = self.deck_area
        else:
            pca = self.player2portrait(_from.owner).portcard_area

        for i, card in enumerate(cards):
            cs = CardSprite(
                parent=pca,
                img=card.ui_meta.image,
            )
            cs.associated_card = card
            csl.append(cs)
        pca.arrange()

    # --- dest ---

    if to.owner is g.me and to.type == to.HANDCARD:
        handcard_update = True
        csl.migrate_to(self.handcard_area)
    else:
        if to.type == to.DROPPEDCARD:
            dropcard_update = True
            ca = self.dropcard_area
            gray = not isinstance(act, (
                actions.DropUsedCard,
            ))
            for cs in csl:
                cs.gray = gray
        else:
            ca = self.player2portrait(to.owner).portcard_area
        csl.migrate_to(ca)
        ca.update()

    if handcard_update: self.handcard_area.update()
    if dropcard_update: self.dropcard_area.update()



def damage_effect(self, act):
    s, t = act.source, act.target
    port = self.player2portrait(t)
    l = t.life
    port.life = l if l > 0 else 0
    port.update()
    self.prompt(u'|c208020ff【%s】|r对|c208020ff【%s】|r造成了%d点伤害。' % (
        s.ui_meta.char_name, t.ui_meta.char_name, act.amount
    ))
    OneShotAnim(common_res.hurt, x=port.x, y=port.y, batch=self.animations)

def heal_effect(self, act):
    t = act.target
    port = self.player2portrait(t)
    l = t.life
    port.life = l if l > 0 else 0
    port.update()
    if act.succeeded:
        self.prompt(u'|c208020ff【%s】|r回复了%d点体力。' % (
            t.ui_meta.char_name, act.amount
        ))

def launch_effect(self, act):
    s, tl = act.source, BatchList(act.target_list)
    for t in tl: self.ray(s, t)
    c = act.card
    from ..characters import Skill
    if isinstance(c, Skill):
        self.prompt(c.ui_meta.effect_string(act))
    elif c:
        self.prompt(u'|c208020ff【%s】|r对|c208020ff【%s】|r使用了|c208020ff%s|r。' % (
            s.ui_meta.char_name,
            u'】|r、|c208020ff【'.join(tl.ui_meta.char_name),
            act.card.ui_meta.name
        ))

def graze_effect(self, act):
    if not act.succeeded: return
    t = act.target
    self.prompt(u'|c208020ff【%s】|r使用了|c208020ff闪|r。' % t.ui_meta.char_name)

def reject_effect(self, act):
    s = u'|c208020ff【%s】|r为|c208020ff【%s】|r受到的|c208020ff%s|r使用了|c208020ff%s|r。' % (
        act.source.ui_meta.char_name,
        act.target.ui_meta.char_name,
        act.target_act.associated_card.ui_meta.name,
        act.associated_card.ui_meta.name,
    )
    self.prompt(s)

def demolition_effect(self, act):
    if not act.succeeded: return
    s = u'|c208020ff【%s】|r卸掉了|c208020ff【%s】|r的|c208020ff%s|r。' % (
        act.source.ui_meta.char_name,
        act.target.ui_meta.char_name,
        act.card.ui_meta.name,
    )
    self.prompt(s)

mapping_actions = ddict(dict, {
    'before': {
        LaunchCard: launch_effect,
        Reject: reject_effect,
    },
    'after': {
        #DrawCards: draw_cards_effect,
        #DrawCardStage: draw_cards_effect,
        #DropCards: drop_cards_gray_effect,
        #DropUsedCard: drop_cards_normal_effect,
        Damage: damage_effect,
        Heal: heal_effect,
        UseGraze: graze_effect,
        Demolition: demolition_effect,
    }
})

def action_effects(_type, self, act):
    cls = act.__class__
    while cls is not object:
        f = mapping_actions[_type].get(cls)
        if f:
            f(self, act)
            return
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

def player_turn_effect(self, p):
    port = self.player2portrait(p)
    if not hasattr(self, 'turn_frame') or not self.turn_frame:
        self.turn_frame = LoopingAnim(
            common_res.turn_frame,
            batch = self.animations
        )
    self.turn_frame.position = (port.x - 6, port.y - 4)
    self.prompt_raw('--------------------\n')

mapping_events = ddict(bool, {
    'action_before': partial(action_effects, 'before'),
    'action_apply': partial(action_effects, 'apply'),
    'action_after': partial(action_effects, 'after'),
    'user_input_start': user_input_start_effects,
    'user_input_finish': user_input_finish_effects,
    'card_migration': card_migration_effects,
    'player_turn': player_turn_effect,
})

def handle_event(self, _type, data):
    f = mapping_events.get(_type)
    if f: f(self, data)
