# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.characters.baseclasses import Character, register_character_to


# -- code --
@register_character_to('special')
class Akari(Character):
    # dummy player for hidden choices
    skills = []
    eventhandlers_required = []
    maxlife = 0
