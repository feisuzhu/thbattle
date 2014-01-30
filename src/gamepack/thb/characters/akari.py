# -*- coding: utf-8 -*-

from .baseclasses import Character, register_character_to


@register_character_to('special')
class Akari(Character):
    # dummy player for hidden choices
    skills = []
    eventhandlers_required = []
    maxlife = 0
