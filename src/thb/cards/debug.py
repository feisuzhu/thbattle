# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game
from thb.actions import Damage, ForEach, UserAction


# -- code --
class MassiveDamageEffect(UserAction):
    def apply_action(self):
        g = Game.getgame()
        g.process_action(Damage(self.source, self.target, 99))
        return True


class MassiveDamage(ForEach):
    action_cls = MassiveDamageEffect
    group_effect = True
