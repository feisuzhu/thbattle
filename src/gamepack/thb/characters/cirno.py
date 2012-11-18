# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *


class PerfectFreeze(TreatAsSkill):
    treat_as = FrozenFrogCard
    def check(self):
        cl = self.associated_cards
        if not (cl and len(cl) == 1): return False
        c  = cl[0]
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        act = c.associated_action
        if not act: return False
        return issubclass(act, (BasicAction, WearEquipmentAction))


class PerfectFreezeHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'calcdistance':
            act, dist = arg
            if not act.source.has_skill(PerfectFreeze): return arg
            if not act.card.is_card(FrozenFrogCard): return arg
            for p in dist:
                dist[p] -= 1

        return arg


@register_character
class Cirno(Character):
    skills = [PerfectFreeze]
    eventhandlers_required = [PerfectFreezeHandler]
    maxlife = 4
