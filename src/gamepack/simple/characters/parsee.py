# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *

class Envy(TreatAsSkill):
    treat_as = DemolitionCard
    def check(self):
        return len(self.associated_cards) == 1

@register_character
class Parsee(Character):
    skills = [Envy]
    eventhandlers_required = []
    maxlife = 4
