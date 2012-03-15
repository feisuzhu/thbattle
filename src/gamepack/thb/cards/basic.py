# -*- coding: utf-8 -*-

from ..actions import *

class BasicAction(UserAction): pass # attack, graze, heal

class Attack(BasicAction):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = UseGraze(target)
        if not g.process_action(graze_action):
            g.process_action(Damage(source, target, amount=self.damage))
            return True
        else:
            return False

class Heal(BasicAction):

    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        source = self.source # target is ignored
        if source.life < source.maxlife:
            source.life = min(source.life + self.amount, source.maxlife)
            return True
        else:
            return False

class UseGraze(UseCard):
    def cond(self, cl):
        from .. import cards
        return len(cl) == 1 and isinstance(cl[0], cards.GrazeCard)
