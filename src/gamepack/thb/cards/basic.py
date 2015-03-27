# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import ActionStage, ActionStageLaunchCard, AskForCard, Damage, DropCards, ActionLimitExceeded
from ..actions import ForEach, GenericAction, LaunchCard, PlayerTurn, UserAction, UseCard
from ..actions import register_eh, user_choose_cards
from game.autoenv import EventHandler, Game


# -- code --
class BasicAction(UserAction):
    pass


class BaseAttack(UserAction):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = Game.getgame()
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
        g = Game.getgame()
        dmg = Damage(self.source, self.target, amount=self.damage)
        g.process_action(dmg)
        return True


class AttackLimitExceeded(ActionLimitExceeded):
    pass


@register_eh
class AttackCardHandler(EventHandler):
    interested = ('action_apply', 'action_before', 'action_shootdown', 'calcdistance')

    def handle(self, evt_type, act):
        # if evt_type == 'action_before' and isinstance(act, PlayerTurn):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            act.target.tags['attack_num'] = 1

        elif evt_type == 'action_apply':
            if isinstance(act, ActionStageLaunchCard):
                from .definition import AttackCard
                if act.card.is_card(AttackCard):
                    src = act.source
                    src.tags['attack_num'] -= 1

        elif evt_type == 'calcdistance':
            src, card, dist = act
            from .definition import AttackCard
            if card.is_card(AttackCard):
                l = self.attack_range_bonus(src)
                for p in dist:
                    dist[p] -= l

        elif evt_type == 'action_shootdown' and isinstance(act, ActionStageLaunchCard):
            from .definition import AttackCard
            if act.card.is_card(AttackCard):
                src = act.source
                if src.tags['freeattack'] >= src.tags['turn_count']:
                    return act

                if src.tags['attack_num'] <= 0:
                    raise AttackLimitExceeded

        return act

    @staticmethod
    def set_freeattack(p):
        p.tags['freeattack'] = p.tags['turn_count']

    @staticmethod
    def cancel_freeattack(p):
        p.tags['freeattack'] = 0

    @staticmethod
    def is_freeattack(p):
        return p.tags['freeattack'] >= p.tags['turn_count']

    @staticmethod
    def attack_range_bonus(p):
        from .equipment import WeaponSkill
        l = [
            s.range - 1 for s in p.skills
            if issubclass(s, WeaponSkill) and p.has_skill(s)
        ]
        return max(0, 0, *l)


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
        from .. import cards
        AskForCard.__init__(self, target, target, cards.AttackCard)

    def process_card(self, card):
        g = Game.getgame()
        return g.process_action(UseCard(self.target, card))

    def ask_for_action_verify(self, p, cl, tl):
        return UseCard(p, cl[0]).can_fire()


class BaseUseGraze(AskForCard):
    def __init__(self, target):
        from .. import cards
        AskForCard.__init__(self, target, target, cards.GrazeCard)


class UseGraze(BaseUseGraze):
    card_usage = 'use'

    def process_card(self, card):
        g = Game.getgame()
        return g.process_action(UseCard(self.target, card))

    def ask_for_action_verify(self, p, cl, tl):
        return UseCard(p, cl[0]).can_fire()


class LaunchGraze(BaseUseGraze):
    card_usage = 'launch'

    def process_card(self, card):
        g = Game.getgame()
        tgt = self.target
        return g.process_action(LaunchCard(tgt, [tgt], card, GrazeAction))

    def ask_for_action_verify(self, p, cl, tl):
        tgt = self.target
        return LaunchCard(tgt, [tgt], cl[0], GrazeAction).can_fire()


class AskForHeal(AskForCard):
    card_usage = 'launch'

    def __init__(self, source, target):
        from .. import cards
        AskForCard.__init__(self, source, target, cards.HealCard)

    def process_card(self, card):
        g = Game.getgame()
        src, tgt = self.source, self.target
        return g.process_action(LaunchCard(tgt, [src], card, card.associated_action or Heal))

    def ask_for_action_verify(self, p, cl, tl):
        src, tgt = self.source, self.target
        card = cl[0]
        return LaunchCard(tgt, [src], card, card.associated_action or Heal).can_fire()


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
        Game.getgame().process_action(SoberUp(tgt, tgt))
        return True


@register_eh
class WineHandler(EventHandler):
    interested = ('action_apply', 'action_before', 'post_choose_target')

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            pact = ForEach.get_actual_action(act) or act
            if getattr(pact, 'in_wine', False):
                act.damage += 1

        elif evt_type == 'post_choose_target':
            act, tl = arg = act

            from ..cards import AttackCard
            if act.card.is_card(AttackCard):
                src = act.source
                if src.tags['wine']:
                    Game.getgame().process_action(SoberUp(src, src))
                    act.card_action.in_wine = True

            return arg

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


class ExinwanEffect(GenericAction):
    # 恶心丸
    card_usage = 'drop'

    def apply_action(self):
        g = Game.getgame()
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
        from .base import Skill
        if any(isinstance(c, Skill) for c in cards): return False
        return True

    def is_valid(self):
        return not self.target.dead


@register_eh
class ExinwanHandler(EventHandler):
    # 恶心丸

    interested = ('card_migration', 'post_card_migration')

    def handle(self, evt_type, arg):
        from .base import VirtualCard, HiddenCard
        from .definition import ExinwanCard

        if evt_type == 'card_migration':
            act, cards, _from, to = arg

            # someone is getting the ExinwanCard
            if to.owner is not None:
                for c in VirtualCard.unwrap(cards):
                    # Exinwan may be HiddenCard here
                    c.exinwan_target = None

                return arg

            # move from None to None do not affect Exinwan's target
            if _from is None or _from.owner is None:
                return arg

            # someone is dropping the ExinwanCard
            for c in VirtualCard.unwrap(cards):
                # Exinwan may be HiddenCard here
                c.exinwan_target = act.source

            return arg

        elif evt_type == 'post_card_migration':
            dropcl = [cl for cl, _, to in arg
                      if to.type == 'droppedcard']

            def invalid(c):
                return c.is_card(VirtualCard) or c.is_card(HiddenCard)

            # cards to dropped area should all unwrapped
            assert not any(invalid(c)
                           for cl in dropcl for c in cl)

            cards = [c for cl in dropcl for c in cl
                     if c.is_card(ExinwanCard)]

            # no same card dropped twice in the same transaction
            assert len(cards) == len(set(cards))

            for c in cards:
                tgt = getattr(c, 'exinwan_target', None)
                if tgt:
                    Game.getgame().process_action(ExinwanEffect(tgt, tgt))

        return arg
