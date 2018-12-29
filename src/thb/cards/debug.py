# -*- coding: utf-8 -*-


# -- stdlib --
# -- third party --
# -- own --
from thb.actions import Damage, ForEach, UserAction


# -- code --
class MassiveDamageEffect(UserAction):
    def apply_action(self):
        g = self.game
        g.process_action(Damage(self.source, self.target, 99))
        return True


class MassiveDamage(ForEach):
    action_cls = MassiveDamageEffect
    group_effect = True
