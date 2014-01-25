# -*- coding: utf-8 -*-
from .baseclasses import Character, register_special_character


@register_special_character
class Akari(Character):
    # dummy player for hidden choices
    skills = []
    eventhandlers_required = []
    maxlife = 0
