# -*- coding: utf-8 -*-

from .. import cards
from ..skill import *

characters = []

class Character(object):
    #skills = []
    #eventhandlers_required = []
    #associated_action = None

    def has_skill(self, skill):
        return skill in self.skills

characters[:] = []

def register_character(cls):
    characters.append(cls)
    return cls
