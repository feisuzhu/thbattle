# -*- coding: utf-8 -*-
from client.ui.base import *
from client.ui.base.interp import *
from client.ui.controls import *

from client.ui import resource as common_res
import resource as gres

import pyglet
from pyglet.gl import *

from gamepack.simple.actions import *

from functools import partial
from collections import defaultdict as ddict

from utils import BatchList

import logging
log = logging.getLogger('SimpleGameUI_Effects')

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

def damage_effect(self, act):
    s, t = act.source, act.target
    port = self.player2portrait(t)
    l = t.life
    port.life = l if l > 0 else 0
    self.prompt(u'%s对%s造成了%d点伤害' % (s.nickname, t.nickname, act.amount))
    OneShotAnim(common_res.hurt, x=port.x, y=port.y, batch=self.animations)

def heal_effect(self, act):
    t = act.target
    port = self.player2portrait(t)
    l = t.life
    port.life = l if l > 0 else 0
    if act.succeeded:
        self.prompt(u'%s回复了%d点体力' % (t.nickname, act.amount))

def launch_effect(self, act):
    s, tl = act.source, BatchList(act.target_list)
    for t in tl: self.ray(s, t)
    self.prompt(u'%s对%s使用了|c208020ff【%s】|r。' % (s.nickname, u'、'.join(tl.nickname), act.card.ui_meta.name))

def graze_effect(self, act):
    if not act.succeeded: return
    t = act.target
    self.prompt(u'%s使用了|c208020ff【闪】|r' % t.nickname)

mapping_actions = ddict(dict, {
    'before': {
        LaunchCard: launch_effect,
    },
    'after': {
        DrawCards: draw_cards_effect,
        DrawCardStage: draw_cards_effect,
        DropCards: drop_cards_gray_effect,
        DropUsedCard: drop_cards_normal_effect,
        Damage: damage_effect,
        Heal: heal_effect,
        UseGraze: graze_effect,
        #Demolition: demolition_effect,
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
    p = input.player
    port = self.player2portrait(p)
    if p is self.current_turn:
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

mapping_events = ddict(bool, {
    'action_before': partial(action_effects, 'before'),
    'action_apply': partial(action_effects, 'apply'),
    'action_after': partial(action_effects, 'after'),
    'user_input_start': user_input_start_effects,
    'user_input_finish': user_input_finish_effects,
    'player_turn': player_turn_effect,
})

def handle_event(self, _type, data):
    f = mapping_events.get(_type)
    if f: f(self, data)
