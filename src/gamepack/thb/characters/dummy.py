# -*- coding: utf-8 -*-
from .baseclasses import Character, register_testing_character


@register_testing_character
class Dummy(Character):
    skills = []
    eventhandlers_required = []
    maxlife = 5
