# -*- coding: utf-8 -*-

from .. import cards

characters = []

class Character(object):
    # skills = []
    # eventhandlers_required = []
    # associated_action = None

    def get_skills(self, skill):
        return [s for s in self.skills if issubclass(s, skill)]

    has_skill = get_skills


def register_character(cls):
    characters.append(cls)
    return cls
