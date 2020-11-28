# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import cast

# -- third party --
# -- own --
from game.base import EventHandler
from thb.actions import ActionStage, ActionStageLaunchCard, AskForCard, Damage, DropCards, ForEach
from thb.actions import GenericAction, LaunchCard, MigrateCardsTransaction, PrepareStage, UseCard
from thb.actions import UserAction, VitalityLimitExceeded, register_eh, ttags, user_choose_cards


# -- code --
class BasicAction(UserAction):
    pass


class BaseAttack(UserAction):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = self.game
        source, target = self.source, self.target
        rst = g.process_action(LaunchGraze(target))
        self1, rst = g.emit_event('attack_aftergraze', (self, not rst))
        assert self1 is self
        assert rst in (False, True)
        if rst:
            g.process_action(Damage(source, target, amount=self.damage))
            return True
        else:
            return False

    def is_valid(self):
        return not self.target.dead


class Attack(BaseAttack, BasicAction):
    pass


class InevitableAttack(Attack):
    def apply_action(self):
        g = self.game
        dmg = Damage(self.source, self.target, amount=self.damage)
        g.process_action(dmg)
        return True


@register_eh
class AttackCardRangeHandler(EventHandler):
    interested = ['calcdistance']

    def handle(self, evt_type, act):
        if evt_type == 'calcdistance':
            src, card, dist = act
            from .definition import AttackCard
            if card.is_card(AttackCard):
                self.fix_attack_range(src, dist)

        return act

    @staticmethod
    def attack_range_bonus(p):
        from .equipment import WeaponSkill
        l = [
            s.range - 1 for s in p.skills
            if issubclass(s, WeaponSkill) and p.has_skill(s)
        ]
        return max(0, 0, *l)

    @classmethod
    def fix_attack_range(cls, src, dist):
        l = cls.attack_range_bonus(src)
        for p in dist:
            dist[p] -= l


@register_eh
class AttackCardVitalityHandler(EventHandler):
    interested = ['action_before', 'action_shootdown']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStageLaunchCard):
            from .definition import AttackCard
            src = act.source
            if act.card.is_card(AttackCard) and not self.is_disabled(src):
                act._['vitality-handler'] = 'already-handled'
                ttags(src)['vitality'] -= 1

        elif evt_type == 'action_shootdown' and isinstance(act, ActionStageLaunchCard):
            from .definition import AttackCard
            if act.card.is_card(AttackCard):
                src = act.source
                if self.is_disabled(src):
                    return act

                if act._['vitality-handler']:
                    return act

                if ttags(src)['vitality'] > 0:
                    return act

                raise VitalityLimitExceeded

        return act

    @staticmethod
    def disable(p):
        ttags(p)['attack_card_vitality'] = True

    @staticmethod
    def enable(p):
        ttags(p)['attack_card_vitality'] = False

    @staticmethod
    def is_disabled(p):
        return ttags(p)['attack_card_vitality']


@register_eh
class VitalityHandler(EventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            ttags(act.source)['vitality'] = 1

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

    def is_valid(self):
        tgt = self.target
        return not tgt.dead and tgt.life < tgt.maxlife


class GrazeAction(BasicAction):

    def apply_action(self):
        return True


class UseAttack(AskForCard):
    card_usage = 'use'

    def __init__(self, target):
        from thb.cards.definition import AttackCard
        AskForCard.__init__(self, target, target, AttackCard)

    def process_card(self, card):
        g = self.game
        return g.process_action(UseCard(self.target, card))

    def ask_for_action_verify(self, p, cl, tl):
        return UseCard(p, cl[0]).can_fire()


class BaseUseGraze(AskForCard):
    def __init__(self, target):
        from thb.cards.definition import GrazeCard
        AskForCard.__init__(self, target, target, GrazeCard)


class UseGraze(BaseUseGraze):
    card_usage = 'use'

    def process_card(self, card):
        g = self.game
        return g.process_action(UseCard(self.target, card))

    def ask_for_action_verify(self, p, cl, tl):
        return UseCard(p, cl[0]).can_fire()


class LaunchGraze(BaseUseGraze):
    card_usage = 'launch'

    def process_card(self, card):
        g = self.game
        tgt = self.target
        return g.process_action(LaunchCard(tgt, [tgt], card, GrazeAction(tgt, tgt)))

    def ask_for_action_verify(self, p, cl, tl):
        tgt = self.target
        return LaunchCard(tgt, [tgt], cl[0], GrazeAction(tgt, tgt)).can_fire()


class AskForHeal(AskForCard):
    card_usage = 'launch'

    def __init__(self, source, target):
        from thb import cards
        AskForCard.__init__(self, source, target, cards.definition.HealCard)

    def process_card(self, card):
        g = self.game
        src, tgt = self.source, self.target
        heal_cls = card.associated_action or Heal
        return g.process_action(LaunchCard(tgt, [src], card, heal_cls(tgt, src)))

    def ask_for_action_verify(self, p, cl, tl):
        src, tgt = self.source, self.target
        card = cl[0]
        heal_cls = card.associated_action or Heal
        return LaunchCard(tgt, [src], card, heal_cls(tgt, src)).can_fire()


class Wine(BasicAction):
    def apply_action(self):
        self.target.tags['wine'] = True
        return True

    def is_valid(self):
        return not self.target.dead


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
        self.game.process_action(SoberUp(tgt, tgt))
        return True


@register_eh
class WineHandler(EventHandler):
    interested = ['action_apply', 'action_before', 'post_choose_target']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            pact = ForEach.get_actual_action(act) or act
            if getattr(pact, 'in_wine', False):
                act.damage += 1

        elif evt_type == 'post_choose_target':
            act, tl = arg = act

            from thb.cards.definition import AttackCard
            if act.card.is_card(AttackCard):
                src = act.source
                if src.tags['wine']:
                    self.game.process_action(SoberUp(src, src))
                    act.card_action.in_wine = True

            return arg

        elif evt_type == 'action_apply' and isinstance(act, PrepareStage):
            src = act.target
            if src.tags['wine']:
                self.game.process_action(SoberUp(src, src))

        elif evt_type == 'action_before' and isinstance(act, Damage):
            if act.cancelled: return act
            if act.amount < 1: return act
            tgt = act.target
            if act.amount >= tgt.life and tgt.tags['wine']:
                g = self.game
                g.process_action(WineRevive(act))

        return act


class Exinwan(BasicAction):
    # 恶心丸
    def apply_action(self):
        return True


class ExinwanEffect(GenericAction):
    # 恶心丸
    card_usage = 'drop'

    def apply_action(self):
        g = self.game
        tgt = self.target
        if tgt.dead:
            return False

        cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))

        if cards:
            g.process_action(DropCards(tgt, tgt, cards))
        else:
            g.process_action(Damage(None, tgt))

        return True

    def cond(self, cards):
        if len(cards) != 2: return False
        from thb.cards.base import Skill
        if any(isinstance(c, Skill) for c in cards): return False
        return True

    def is_valid(self):
        return not self.target.dead


@register_eh
class ExinwanHandler(EventHandler):
    # 恶心丸

    interested = ['post_card_migration']

    def handle(self, evt_type, arg) -> None:
        from thb.cards.base import VirtualCard, HiddenCard
        from thb.cards.definition import ExinwanCard

        if evt_type == 'post_card_migration':
            moves = cast(MigrateCardsTransaction, arg).movements
            moves = [m for m in moves if m.to.type == 'droppedcard']

            # cards to dropped area should all unwrapped
            assert not any(
                m.card.is_card(VirtualCard) or m.card.is_card(HiddenCard)
                for m in moves
            )

            moves = [m for m in moves if m.card.is_card(ExinwanCard)]

            # no same card dropped twice in the same transaction
            assert len(moves) == len(set(m.card for m in moves))

            for m in moves:
                tgt = m.trans.action.source
                if tgt and not tgt.dead:
                    act = ExinwanEffect(tgt, tgt)
                    act.associated_card = m.card
                    self.game.process_action(act)

        return arg
