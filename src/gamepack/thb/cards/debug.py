# -*- coding: utf-8  -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb.actions import Damage, UserAction, ForEach
from game.autoenv import Game


# -- code --
class MassiveDamageEffect(UserAction):
    def apply_action(self):
        g = Game.getgame()
        g.process_action(Damage(self.source, self.target, 99))
        return True


class MassiveDamage(ForEach):
    action_cls = MassiveDamageEffect
    group_effect = True
