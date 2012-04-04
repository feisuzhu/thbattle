# -*- coding: utf-8 -*-

from cards.base import VirtualCard

class Skill(VirtualCard):

    def __init__(self, cards=None):
        self.associated_cards = cards
        VirtualCard.__init__(self)

    def check(self): # override this
        return False

    # target = xxx
    # associated_action = xxx
    # instance var: associated_cards = xxx

class TreatAsSkill(Skill):
    treat_as = None

    def check(self):
        return False

    def is_card(self, cls):
        if issubclass(self.treat_as, cls): return True
        return isinstance(self, cls)

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            tr = object.__getattribute__(self, 'treat_as')
            return getattr(tr, name)
