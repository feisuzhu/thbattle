# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *

class TreatAsDemolition(TreatAsAction):
    treat_as = DemolitionCard
    @classmethod
    def cond(cls, actor, cards):
        return len(cards) == 1

class Envy(Skill):
    associated_action = TreatAsDemolition

class Parsee(Character):
    skills = [Envy]
    eventhandlers_required = []
    maxlife = 4
