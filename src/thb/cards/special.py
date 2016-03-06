# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game
from thb.actions import DrawCards, UserAction, migrate_cards


# -- code --
class CollectPPoint(UserAction):
    def apply_action(self):
        c = self.associated_card
        tgt = self.target
        g = Game.getgame()
        g.emit_event('collect_ppoint', (self.target.account, c.number))
        migrate_cards([c], g.deck.collected_ppoints, unwrap=True)
        g.process_action(DrawCards(tgt, 1))
        return True
