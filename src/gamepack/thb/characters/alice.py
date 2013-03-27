# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *


class DollManipulation(Skill):
    associated_action = None
    target = t_None


class DollManipulationHandler(EventHandler):
    execute_after = ('ElementalReactorHandler', )
    def handle(self, evt_type, tgt):
        if evt_type == 'action_stage_action':
            tags = tgt.tags
            if not tgt.has_skill(DollManipulation): return tgt
            AttackCardHandler.set_freeattack(tgt)

        return tgt


class DollCrusader(TreatAsSkill):
    treat_as = DollControlCard
    def check(self):
        cl = self.associated_cards
        if not cl and len(cl) == 1: return False
        c = cl[0]
        if c.resides_in.type not in (
            'handcard',
            'showncard',
            'equips',
        ): return False

        cat = getattr(c, 'equipment_category', None)
        if cat == 'accessories': return True
        return False


@register_character
class Alice(Character):
    skills = [DollManipulation, DollCrusader]
    eventhandlers_required = [DollManipulationHandler]
    maxlife = 4
