# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..cards import Card, FrozenFrogCard, Skill, TreatAs
from .baseclasses import Character, register_character_to
from game.autoenv import EventHandler


# -- code --
class PerfectFreeze(TreatAs, Skill):
    treat_as = FrozenFrogCard
    skill_category = ('character', 'active')

    def check(self):
        cl = self.associated_cards
        if not (cl and len(cl) == 1): return False
        c = cl[0]
        if c.resides_in.type not in (
            'cards', 'showncards', 'equips'
        ): return False
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        if 'skill' in c.category: return False
        return bool(set(c.category) & {'basic', 'equipment'})


class PerfectFreezeHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'calcdistance':
            src, card, dist = arg
            if not src.has_skill(PerfectFreeze): return arg
            if not card.is_card(FrozenFrogCard): return arg
            for p in dist:
                dist[p] -= 1

        return arg


@register_character_to('common', '-kof')
class Cirno(Character):
    skills = [PerfectFreeze]
    eventhandlers_required = [PerfectFreezeHandler]
    maxlife = 4
