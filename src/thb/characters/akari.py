# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb.cards import Skill, t_None
from thb.characters.baseclasses import Character, register_character_to


# -- code --
class AkariSkill(Skill):
    associated_action = None
    skill_category = ()
    target = t_None


@register_character_to('special')
class Akari(Character):
    # dummy player for hidden choices
    skills = [AkariSkill]
    eventhandlers_required = []
    maxlife = 0
