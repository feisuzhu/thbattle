# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..skill import *
from ..cards import *

class DollManipulation(Skill):
    associated_action = None
    target = t_None

class DollManipulationHandler(EventHandler):
    execute_after = (AttackCardHandler, )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            tgt = act.actor
            if tgt.has_skill(DollManipulation):
                act.actor.tags['attack_num'] = 10000
        return act

@register_character
class Alice(Character):
    skills = [DollManipulation]
    eventhandlers_required = [DollManipulationHandler]
    maxlife = 4
