# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game
from thb.actions import DrawCards, UserAction, ttags
from thb.cards import Skill, t_Self
from thb.characters.baseclasses import Character, register_character_to


# -- code --
class FindAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        cards = self.associated_card.associated_cards
        n = len(cards)
        # card will be dropped at LaunchCard
        # g.process_action(DropCards(tgt, tgt, cards))
        tgt = self.target
        g.process_action(DrawCards(tgt, n))
        ttags(tgt)['find'] = True
        return True

    def is_valid(self):
        try:
            p = self.target
            if ttags(p)['find']:
                return False

            g = Game.getgame()
            cards = self.associated_card.associated_cards
            if not 0 < len(cards) <= len([i for i in g.players if not i.dead]):
                return False

            return True

        except AttributeError:  # well, some cards are skill?
            return False


class Find(Skill):
    associated_action = FindAction
    skill_category = ('character', 'active')
    target = t_Self
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        return cl and all(
            c.resides_in is not None and
            c.resides_in.type in (
                'cards', 'showncards', 'equips'
            ) for c in self.associated_cards
        )


@register_character_to('common')
class Koakuma(Character):
    skills = [Find]
    eventhandlers_required = []
    maxlife = 4
