# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Mijincihangzhan(Skill):
    # 迷津慈航斩
    # compulsory skill, just a tag.
    associated_action = None
    target = t_None

class MijincihangzhanAttack(Attack):
    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target

        for i in xrange(2):
            graze_action = UseGraze(target)
            if not g.process_action(graze_action):
                break
        else:
            return False

        g.process_action(Damage(source, target, amount=self.damage))
        return True

class MijincihangzhanHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Attack):
            if act.source.has_skill(Mijincihangzhan):
                act.__class__ = MijincihangzhanAttack

        return act

@register_character
class Youmu(Character):
    skills = [Mijincihangzhan]
    eventhandlers_required = [MijincihangzhanHandler]
    maxlife = 4
