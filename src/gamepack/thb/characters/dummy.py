# -*- coding: utf-8 -*-
from .baseclasses import Character, register_character_to


@register_character_to('testing')
class Dummy(Character):
    skills = []
    eventhandlers_required = []
    maxlife = 5
