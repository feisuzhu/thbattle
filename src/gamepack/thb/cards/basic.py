# -*- coding: utf-8 -*-

from ..actions import *

class BasicAction(UserAction): pass # attack, graze, heal

class BaseAttack(BasicAction):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = UseGraze(target)
        if not g.process_action(graze_action):
            dmg = Damage(source, target, amount=self.damage)
            dmg.associated_action = self
            g.process_action(dmg)
            return True
        else:
            return False

class Attack(BaseAttack): pass

@register_eh
class AttackCardHandler(EventHandler):
    execute_before = (DistanceValidator,)
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            act.actor.tags['attack_num'] = 1
        elif evt_type == 'action_after' and isinstance(act, LaunchCard):
            from .definition import AttackCard
            if isinstance(act.card, AttackCard):
                act.target_list[0].tags['attack_num'] -= 1
        elif evt_type == 'action_after' and isinstance(act, CalcDistance):
            card = act.card
            from .definition import AttackCard
            if isinstance(card, AttackCard):
                from .equipment import WeaponSkill
                source = act.source
                if source.tags['attack_num'] <= 0:
                    act.correction -= 10000

                l = []
                for s in source.skills:
                    if issubclass(s, WeaponSkill):
                        l.append(s.range - 1)
                if l: act.correction += min(l)

        return act

class Heal(BasicAction):

    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        target = self.target
        if target.life < target.maxlife:
            target.life = min(target.life + self.amount, target.maxlife)
            return True
        else:
            return False

class UseGraze(UseCard):
    def cond(self, cl):
        from .. import cards
        t = self.target
        return (
            len(cl) == 1 and
            isinstance(cl[0], cards.GrazeCard) and
            cl[0].resides_in.owner is t
        )

class UseAttack(UseCard):
    def cond(self, cl):
        from .. import cards
        t = self.target
        return (
            len(cl) == 1 and
            isinstance(cl[0], cards.AttackCard) and
            cl[0].resides_in.owner is t
        )
