from client.ui.base import *
from client.ui.base.interp import *
from client.ui.controls import *

from client.ui import resource as common_res
import resource as gres

import pyglet
from pyglet.gl import *

from gamepack.simple.actions import *

from functools import partial

import logging
log = logging.getLogger('SimpleGameUI_Effects')

card_img = dict(
    attack=gres.card_attack,
    graze=gres.card_graze,
    heal=gres.card_heal,
    hidden=common_res.card_hidden,
)

def draw_cards_effect(self, evt): # here self is the SimpleGameUI instance
    if evt.target is self.game.me:
        cards = evt.cards
        hca = self.handcard_area
        ax, ay = hca.abs_coords()
        csl = [CardSprite(
                parent=hca, x=410-ax, y=300-ay,
                img = card_img.get(c.type),
        ) for c in cards]
        self.handcard_area.add_cards(csl)
    else: # FIXME: not exactly the effect
        p = self.player2portrait(evt.target)
        x, y = p.x + p.width/2, p.y + p.height/2

        n = len(evt.cards)
        if n > 1:
            w = 1.5 * CardSprite.width
            step = (w-91)/(n-1)
        else:
            w = CardSprite.width
            step = 0

        def self_destroy(obj, desc):
            obj.delete()

        sy = -CardSprite.height/2
        for i, card in enumerate(evt.cards):
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
            cs.img = card_img.get(card.type)

def drop_cards_effect(gray, self, evt):
    if evt.target is self.game.me:
        csl = self.handcard_area.get_cards(evt.card_indices)
        csl.reverse()
        for c in csl:
            c.migrate_to(self.dropcard_area)
            c.gray = gray
        self.dropcard_area.add_cards(csl)
    else:
        p = self.player2portrait(evt.target)
        x, y = p.x + p.width/2, p.y + p.height/2
        shift = (len(evt.cards)+1)*CardSprite.width/2
        csl = []
        for i, card in enumerate(evt.cards):
            cs = CardSprite(
                parent=self, x=x-shift+i*CardSprite.width/2,
                y=y-CardSprite.height/2, img=card_img.get(card.type),
            )
            cs.gray = gray
            cs.migrate_to(self.dropcard_area)
            csl.append(cs)
        self.dropcard_area.add_cards(csl)

drop_cards_gray_effect = partial(drop_cards_effect, True)
drop_cards_normal_effect = partial(drop_cards_effect, False)

def damage_effect(self, evt):
    p = evt.target
    port = self.player2portrait(p)
    l = p.gamedata.life
    port.life = l if l > 0 else 0

def heal_effect(self, evt):
    p = evt.target
    port = self.player2portrait(p)
    l = p.gamedata.life
    port.life = l if l > 0 else 0

mapping = {
    DrawCards: draw_cards_effect,
    DrawCardStage: draw_cards_effect,
    DropCardIndex: drop_cards_gray_effect,
    DropUsedCard: drop_cards_normal_effect,
    Damage: damage_effect,
    Heal: heal_effect,
}
