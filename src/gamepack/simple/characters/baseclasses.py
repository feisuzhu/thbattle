# -*- coding: utf-8 -*-

from .. import cards

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

class Skill(cards.Card):
    __eq__ = object.__eq__
    __ne__ = object.__ne__
    __hash__ = object.__hash__

    sort_index = 0

    def __init__(self, actor, cards):
        self.actor = actor
        self.associated_cards = cards

    def __data__(self):
        return {
            'skill_type': self.__class__.__name__,
            'cards': self.associated_cards,
        }

    def _zero(self, *a):
        return 0

    def check(self): # override this
        return False
    syncid = property(_zero, _zero)

    @classmethod
    def unwrap(cls, skill):
        l = []
        sl = skill[:]
        while sl:
            s = sl.pop()
            try:
                sl.extend(s.associated_cards)
            except AttributeError:
                l.append(s)
        return l

    def sync(self, data):
        assert data['skill_type'] == self.__class__.__name__
        for c, d in zip(self.associated_cards, data['cards']):
            c.sync(d)

    # target = xxx
    # associated_action = xxx
    # associated_cards = xxx

class _TreatAsSkillMeta(type):
    def __new__(cls, clsname, bases, _dict):
        if not _dict.has_key('treat_as'):
            raise Exception("You must specify 'treat_as' attrib!")
        ta = _dict['treat_as']
        ta = (ta, ) if ta else ()
        ncls = type.__new__(cls, clsname, bases + ta, _dict)
        return ncls

class TreatAsSkill(Skill):
    __metaclass__ = _TreatAsSkillMeta
    treat_as = None

    def check(self):
        return False
