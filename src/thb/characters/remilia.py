# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Sequence, Any
# -- third party --
# -- own --
from thb.actions import ActionShootdown, Damage, GenericAction, LaunchCard, PrepareStage, UserAction
from thb.cards.base import Card, DummyCard, Skill, t_None
from thb.cards.classes import Attack, AttackCard, Heal, InevitableAttack
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class SpearTheGungnir(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class SpearTheGungnirAction(GenericAction):
    def __init__(self, act):
        self.act = act
        self.source = act.source
        self.target = act.target

    def apply_action(self):
        self.act.__class__ = InevitableAttack
        return True


class SpearTheGungnirHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['ScarletRhapsodySwordHandler']
    execute_after = ['HakuroukenEffectHandler', 'HouraiJewelHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Attack):
            src = act.source
            if not src.has_skill(SpearTheGungnir): return act
            if isinstance(act, InevitableAttack): return act

            tgt = act.target

            while True:
                if tgt.life > src.life: break
                if len(tgt.cards) + len(tgt.showncards) < len(src.cards) + len(src.showncards): break
                return act

            g = self.game
            if g.user_input([act.source], ChooseOptionInputlet(self, (False, True))):
                g.process_action(SpearTheGungnirAction(act))

        return act


class VampireKiss(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class VampireKissAction(GenericAction):
    def apply_action(self):
        return self.game.process_action(
            Heal(self.target, self.source)
        )


class VampireKissHandler(THBEventHandler):
    interested = ['action_apply', 'calcdistance']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not (src and src.has_skill(VampireKiss)): return act
            if src.life >= src.maxlife: return act
            g = self.game
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            card = pact.associated_card
            if (not card) or card.color != Card.RED: return act
            g.process_action(VampireKissAction(src, tgt))

        elif evt_type == 'calcdistance':
            src, card, dist = act

            if not card.is_card(AttackCard): return act
            if not src.has_skill(VampireKiss): return act
            if card.color != Card.RED: return act

            for p in dist:
                dist[p] -= 99999

        return act


class ScarletMistAttackLimit(ActionShootdown):
    pass


class ScarletMistHandler(THBEventHandler):
    interested = [
        'action_after',
        'action_apply',
        'action_shootdown',
        'post_calcdistance',
    ]

    def handle(self, evt_type, act):
        if evt_type == 'action_shootdown' and isinstance(act, LaunchCard):
            if act.bypass_check: return act
            c = act.card
            if not c.is_card(AttackCard): return act

            src, tgt  = act.source, act.target
            if not src.tags['scarlet_mist'] == 'nerf':
                return act

            dist = LaunchCard.calc_raw_distance(src, DummyCard())
            if dist[tgt] > 1:
                raise ScarletMistAttackLimit

        elif evt_type == 'post_calcdistance':
            src, c, dist = act

            if not c.is_card(AttackCard):
                return act

            if src.tags['scarlet_mist'] != 'buff':
                return act

            for k in dist:
                dist[k] = 0

        elif evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if not (src and src.tags['scarlet_mist'] == 'buff'): return act
            if src.life >= src.maxlife: return act

            g = self.game
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            if not pact.associated_card: return act

            g.process_action(Heal(src, src, act.amount))

        elif evt_type == 'action_apply' and isinstance(act, PrepareStage):
            tgt = act.target
            if not tgt.has_skill(ScarletMist): return act
            if not tgt.tags['scarlet_mist']: return act
            g = self.game
            g.process_action(ScarletMistEndAction(tgt, tgt))

        return act


class ScarletMistAction(UserAction):
    def apply_action(self):
        src, tl = self.source, self.target_list
        src.tags['scarlet_mist_used'] = True
        g = self.game
        for p in g.players:
            p.tags['scarlet_mist'] = 'nerf'
        for p in tl:
            p.tags['scarlet_mist'] = 'buff'

        return True

    def is_valid(self):
        src = self.source
        return not src.tags['scarlet_mist_used']


class ScarletMistEndAction(GenericAction):
    def apply_action(self):
        g = self.game
        for p in g.players:
            p.tags['scarlet_mist'] = False

        return True


class ScarletMist(Skill):
    associated_action = ScarletMistAction
    skill_category = ['character', 'active', 'once', 'boss']

    def check(self) -> bool:
        return not len(self.associated_cards)

    def target(self, g: Any, src: Character, tl: Sequence[Character]):
        from thb.thbrole import THBRoleRole
        n = sum(i == THBRoleRole.ACCOMPLICE for i in g.roles.values())
        n -= sum(ch.dead and g.roles[ch.player] == THBRoleRole.ACCOMPLICE for ch in g.players)

        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(src)
        except ValueError:
            pass

        tl.insert(0, src)
        return (tl[:n+1], bool(len(tl)))


@register_character_to('common', 'boss')
class Remilia(Character):
    skills = [SpearTheGungnir, VampireKiss]
    boss_skills = [ScarletMist]
    eventhandlers = [SpearTheGungnirHandler, VampireKissHandler, ScarletMistHandler]
    maxlife = 4
