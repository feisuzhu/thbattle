# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *

class DollManipulation(Skill):
    associated_action = None
    target = t_None

class DollManipulationHandler(EventHandler):
    execute_after = ('AttackCardHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            tgt = act.target
            if tgt.has_skill(DollManipulation):
                act.target.tags['attack_num'] = 10000
        return act

class DollCrusader(TreatAsSkill):
    treat_as = DollControlCard
    def check(self):
        cl = self.associated_cards
        if not cl and len(cl) == 1: return False
        c = cl[0]
        if c.resides_in.type not in (
            CardList.HANDCARD,
            CardList.SHOWNCARD,
            CardList.EQUIPS,
        ): return False

        cat = getattr(c, 'equipment_category', None)
        if cat == 'accessories': return True
        return False

@register_character
class Alice(Character):
    skills = [DollManipulation, DollCrusader]
    eventhandlers_required = [DollManipulationHandler]
    maxlife = 4
