# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *


class PerfectFreeze(TreatAsSkill):
    treat_as = FrozenFrogCard
    def check(self):
        cl = self.associated_cards
        if not (cl and len(cl) == 1): return False
        c = cl[0]
        if not c.resides_in.type in (
            'handcard', 'showncard', 'equips'
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


@register_character
class Cirno(Character):
    skills = [PerfectFreeze]
    eventhandlers_required = [PerfectFreezeHandler]
    maxlife = 4
