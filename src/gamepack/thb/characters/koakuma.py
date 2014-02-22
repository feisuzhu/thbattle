# -*- coding: utf-8 -*-
from game.autoenv import Game
from .baseclasses import Character, register_character
from ..actions import DrawCards, UserAction
from ..cards import Skill, t_Self


class FindAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        cards = self.associated_card.associated_cards
        n = len(cards)
        # card will be dropped at LaunchCard
        #g.process_action(DropCards(self.target, cards))
        tgt = self.target
        g.process_action(DrawCards(tgt, n))
        tgt.tags['find_tag'] = tgt.tags['turn_count']
        return True

    def is_valid(self):
        try:
            p = self.target
            if p.tags.get('turn_count', 0) <= p.tags.get('find_tag', 0):
                return False

            return True

        except AttributeError:  # well, some cards are skill?
            return False


class Find(Skill):
    associated_action = FindAction
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


@register_character
class Koakuma(Character):
    skills = [Find]
    eventhandlers_required = []
    maxlife = 4
