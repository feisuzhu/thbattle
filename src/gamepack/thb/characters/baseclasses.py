# -*- coding: utf-8 -*-

from .. import cards
from game.autoenv import GameObject

characters = []
ex_characters = []

class Character(GameObject):
    # skills = []
    # eventhandlers_required = []
    # associated_action = None

    def get_skills(self, skill):
        return [s for s in self.skills if issubclass(s, skill)]

    has_skill = get_skills


def register_character(cls):
    characters.append(cls)
    return cls

def register_ex_character(cls):
    ex_characters.append(cls)
    return cls
