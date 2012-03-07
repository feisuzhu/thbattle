# -*- coding: utf-8 -*-

characters = []

class CharacterMetaclass(type):
    def __new__(cls, clsname, bases, _dict):
        ncls = type.__new__(cls, clsname, bases, _dict)
        characters.append(ncls)
        return ncls

class Character(object):
    __metaclass__ = CharacterMetaclass
    #skills = []
    #eventhandlers_required = []
    #associated_action = None

    def has_skill(self, skill):
        return skill in self.skills

characters[:] = []

class Skill(object):
    sort_index = 0
