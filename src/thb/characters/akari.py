# -*- coding: utf-8 -*-

# -- stdlib --
from typing import List, Type, ClassVar

# -- third party --
# -- own --
from thb.cards.base import Skill, t_None
from thb.characters.base import Character, register_character_to
from thb.mode import THBEventHandler


# -- code --
class AkariSkill(Skill):
    associated_action = None
    skill_category: List[str] = []
    target = t_None


@register_character_to('special')
class Akari(Character):
    # dummy player for hidden choices
    skills = [AkariSkill]
    eventhandlers: ClassVar[List[Type[THBEventHandler]]] = []
    maxlife = 0
