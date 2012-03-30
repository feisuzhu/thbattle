# -*- coding: utf-8 -*-

from cards.base import VirtualCard

class Skill(VirtualCard):

    def __init__(self, actor, cards):
        self.actor = actor
        self.associated_cards = cards
        VirtualCard.__init__(self)

    def check(self): # override this
        return False

    # target = xxx
    # associated_action = xxx
    # instance var: associated_cards = xxx

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
