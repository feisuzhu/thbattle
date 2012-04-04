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
        elif evt_type == 'action_after':
            if isinstance(act, LaunchCard):
                from .definition import AttackCard
                if act.card.is_card(AttackCard):
                    act.source.tags['attack_num'] -= 1
            elif isinstance(act, ActionStage):
                act.actor.tags['attack_num'] = 10000
            elif isinstance(act, CalcDistance):
                card = act.card
                from .definition import AttackCard
                if card.is_card(AttackCard):
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
            cl[0].is_card(cards.GrazeCard) and
            cl[0].resides_in.owner is t
        )

class UseAttack(UseCard):
    def cond(self, cl):
        from .. import cards
        t = self.target
        return (
            len(cl) == 1 and
            cl[0].is_card(cards.AttackCard) and
            cl[0].resides_in.owner is t
        )

class Wine(BasicAction):
    def apply_action(self):
        self.target.tags['wine'] = True
        return True

@register_eh
class WineHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            src = act.source
            if src.tags.get('wine', False):
                act.damage += 1
                src.tags['wine'] = False
        elif evt_type == 'action_apply' and isinstance(act, ActionStage):
            act.actor.tags['wine'] = False
        return act

class Exinwan(UserAction):
    # 恶心丸
    def apply_action(self):
        return True

@register_eh
class ExinwanHandler(EventHandler):
    # 恶心丸
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DropCards):
            from .definition import ExinwanCard
            cards = [c for c in act.cards_before_unwrap if c.is_card(ExinwanCard)]
            if cards:
                g = Game.getgame()
                pact = g.action_stack[0]
                if isinstance(pact, DropCardStage):
                    target = pact.target
                else:
                    target = pact.source

                cats = [
                    target.cards,
                    target.showncards,
                    target.equips,
                ]
                for i in xrange(len(cards)):
                    cards = user_choose_card(self, target, self.cond, cats)
                    if cards:
                        g.process_action(DropCards(target=target, cards=cards))
                    else:
                        g.process_action(Damage(source=None, target=target))
        return act

    def cond(self, cards):
        if len(cards) != 2: return False
        from ..skill import Skill
        if any(isinstance(c, Skill) for c in cards): return False
        return True
