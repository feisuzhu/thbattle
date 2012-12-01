# -*- coding: utf-8 -*-

from ..actions import *

class BasicAction(UserAction): pass # attack, graze, heal

class BaseAttack(Action):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = LaunchGraze(target)
        if not g.process_action(graze_action):
            dmg = Damage(source, target, amount=self.damage)
            dmg.associated_action = self
            g.process_action(dmg)
            return True
        else:
            return False

class Attack(BaseAttack, BasicAction): pass

class InevitableAttack(Attack):
    def apply_action(self):
        g = Game.getgame()
        dmg = Damage(self.source, self.target, amount=self.damage)
        g.process_action(dmg)
        return True

@register_eh
class AttackCardHandler(EventHandler):
    def handle(self, evt_type, act):
        #if evt_type == 'action_before' and isinstance(act, PlayerTurn):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            act.target.tags['attack_num'] = 1

        elif evt_type == 'action_after':
            if isinstance(act, ActionStageLaunchCard):
                from .definition import AttackCard
                if act.card.is_card(AttackCard):
                    act.source.tags['attack_num'] -= 1

        elif evt_type == 'calcdistance':
            lc, dist = act
            card = lc.card
            from .definition import AttackCard
            if card.is_card(AttackCard):
                from .equipment import WeaponSkill
                src = lc.source

                l = [s.range - 1 for s in src.skills if issubclass(s, WeaponSkill)]
                if not l: return act
                l = min(l)

                for p in dist:
                    dist[p] -= l

        elif evt_type == 'action_can_fire' and isinstance(act[0], ActionStageLaunchCard):
            lc, rst = act
            from .definition import AttackCard
            from .equipment import ElementalReactorSkill
            if lc.source.has_skill(ElementalReactorSkill): return act
            if lc.card.is_card(AttackCard) and lc.source.tags['attack_num'] <= 0:
                return (lc, False)

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

class BaseUseGraze(UseCard):
    def cond(self, cl):
        from .. import cards
        t = self.target
        return (
            len(cl) == 1 and
            cl[0].is_card(cards.GrazeCard) and
            (cl[0].is_card(cards.VirtualCard) or cl[0].resides_in.owner is t)
        )

class UseGraze(BaseUseGraze):
    pass

class LaunchGraze(BaseUseGraze):
    pass

class UseAttack(UseCard):
    def cond(self, cl):
        from .. import cards
        t = self.target
        return (
            len(cl) == 1 and
            cl[0].is_card(cards.AttackCard) and
            (cl[0].is_card(cards.VirtualCard) or cl[0].resides_in.owner is t)
        )

class UseHeal(UseCard):
    def cond(self, cl):
        from .. import cards
        t = self.target
        return (
            len(cl) == 1 and
            cl[0].is_card(cards.HealCard) and
            (cl[0].is_card(cards.VirtualCard) or cl[0].resides_in.owner is t)
        )

class Wine(BasicAction):
    def apply_action(self):
        self.target.tags['wine'] = True
        return True

class SoberUp(GenericAction):
    def apply_action(self):
        self.target.tags['wine'] = False
        return True

class WineRevive(GenericAction):
    def __init__(self, act):
        self.act = act
        self.source = act.target
        self.target = act.target

    def apply_action(self):
        self.act.amount -= 1
        tgt = self.target
        Game.getgame().process_action(SoberUp(tgt, tgt))
        return True

@register_eh
class WineHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            src = act.source
            if src.tags['wine']:
                act.damage += 1
        elif evt_type == 'action_after' and isinstance(act, LaunchCard):
            from ..cards import AttackCard
            if act.card.is_card(AttackCard):
                src = act.source
                if src.tags['wine']:
                    Game.getgame().process_action(SoberUp(src, src))
        elif evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            src = act.target
            if src.tags['wine']:
                Game.getgame().process_action(SoberUp(src, src))
        elif evt_type == 'action_before' and isinstance(act, Damage):
            if act.cancelled: return act
            if act.amount < 1: return act
            tgt = act.target
            if act.amount >= tgt.life and tgt.tags['wine']:
                g = Game.getgame()
                g.process_action(WineRevive(act))
        return act

class Exinwan(BasicAction):
    # 恶心丸
    def apply_action(self):
        return True

@register_eh
class ExinwanHandler(EventHandler):
    # 恶心丸
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCards):
            for c in act.cards:
                c.exinwan_lastin = c.resides_in.type
            return act

        elif evt_type == 'action_after' and isinstance(act, DropCards):
            from .definition import ExinwanCard
            from .base import CardList, VirtualCard
            typelist = ('handcard', 'showncard', 'equips')
            cards = [c for c in act.cards if getattr(c, 'exinwan_lastin', None) in typelist]
            cards = VirtualCard.unwrap(cards)
            cards = [c for c in cards if c.is_card(ExinwanCard)]
            if cards:
                g = Game.getgame()
                pact = g.action_stack[-1]

                target = pact.source

                cats = [
                    target.cards,
                    target.showncards,
                    target.equips,
                ]
                for i in xrange(len(cards)):
                    if target.dead: return act
                    cards = user_choose_cards(self, target, cats)
                    if cards:
                        g.process_action(DropCards(target=target, cards=cards))
                    else:
                        g.process_action(Damage(source=None, target=target))
        return act

    def cond(self, cards):
        if len(cards) != 2: return False
        from .base import Skill
        if any(isinstance(c, Skill) for c in cards): return False
        return True
