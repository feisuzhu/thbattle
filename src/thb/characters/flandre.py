# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import ActionStageLaunchCard, Damage, DrawCardStage, GenericAction, PlayerDeath, FinalizeStage
from thb.actions import PlayerTurn, register_eh, ttags, PrepareStage, user_choose_cards, DropCards
from thb.cards import ActionLimitExceeded, AttackCard, AttackCardVitalityHandler, BaseAttack
from thb.cards import BaseDuel, DuelCard, ElementalReactorSkill, Skill, UserAction, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class CriticalStrike(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class CriticalStrikeAction(GenericAction):
    def apply_action(self):
        return True


class CriticalStrikeDropAction(GenericAction):
    card_usage = 'drop'

    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.cards = []

    def apply_action(self):
        tgt = self.target
        if tgt.dead: return False

        g = Game.getgame()
        cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        if cards:
            g.process_action(DropCards(tgt, tgt, cards=cards))
        else:
            from itertools import chain
            cards = list(chain(tgt.cards, tgt.showncards, tgt.equips))[-1:]
            g.players.reveal(cards)
            g.process_action(DropCards(tgt, tgt, cards=cards))

        self.cards = cards
        return True

    def cond(self, cards):
        tgt = self.target
        if not len(cards) == 1:
            return False

        if not all(c.resides_in in (tgt.cards, tgt.showncards, tgt.equips) for c in cards):
            return False

        from thb.cards import Skill
        if any(c.is_card(Skill) for c in cards):
            return False

        return True


class CriticalStrikeLimit(ActionLimitExceeded):
    pass


class CriticalStrikeHandler(EventHandler):
    interested = ('action_apply', 'action_before', 'action_after', 'action_shootdown', 'action_stage_action')
    execute_after = (
        'AttackCardHandler',
        'FrozenFrogHandler',
        'ElementalReactorHandler',
        'ReversedScalesHandler',
    )
    execute_before = (
        'MomijiShieldHandler',
        'WineHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, PrepareStage):
            ttags(act.target)['flan_targets'] = []

        elif evt_type == 'action_before' and isinstance(act, FinalizeStage):
            if ttags(act.target)['flan_cs']:
                g = Game.getgame()
                tgt = act.target
                g.process_action(CriticalStrikeDropAction(tgt, tgt))

        elif evt_type == 'action_apply' and isinstance(act, BaseAttack):
            src, tgt = act.source, act.target
            if not self.in_critical_strike(src):
                return act

            if isinstance(act, BaseAttack):
                g = Game.getgame()
                g.process_action(CriticalStrikeAction(src, tgt))
                ttags(src)['flan_targets'].append(tgt)
                act.damage += 1

        elif evt_type == 'action_before' and isinstance(act, Damage):
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, BaseDuel):
                return act

            src, tgt = act.source, act.target

            if not self.in_critical_strike(src):
                return act

            g.process_action(CriticalStrikeAction(src, tgt))
            act.amount += 1

        elif evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not self.in_critical_strike(src):
                return act
            ttags(src)['flan_cs'] = True

        elif evt_type == 'action_before' and isinstance(act, ActionStageLaunchCard):
            src = act.source
            if not self.in_critical_strike(src):
                return act

            if act.card.is_card(AttackCard):
                act.vitality_consumed = True
                src.tags['vitality'] -= 1

        elif evt_type == 'action_shootdown':
            if not isinstance(act, ActionStageLaunchCard): return act
            c = act.card
            src = act.source
            if not self.in_critical_strike(src): return act
            if not c.is_card(AttackCard): return act
            if src.has_skill(ElementalReactorSkill): return act
            if src.tags['vitality'] > 0: return act
            if getattr(act, 'vitality_consumed', False): return act
            if set(act.target_list) & set(ttags(src)['flan_targets']):
                raise CriticalStrikeLimit

            return act

        elif evt_type == 'action_stage_action':
            tgt = act
            if not self.in_critical_strike(tgt): return act
            AttackCardVitalityHandler.disable(tgt)

        return act

    def in_critical_strike(self, p):
        return (
            Game.getgame().current_player is p and
            p.has_skill(CriticalStrike)
        )


class Exterminate(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ExterminateAction(UserAction):

    def apply_action(self):
        tgt = self.target
        tgt.tags['exterminate'] = True
        for s in tgt.skills:
            if 'character' in s.skill_category:
                tgt.disable_skill(s, 'exterminate')

        return True


class ExterminateHandler(EventHandler):
    interested = ('choose_target',)

    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            act, tl = arg
            src = act.source
            g = Game.getgame()

            if not src.has_skill(Exterminate):
                return arg

            c = act.card
            if not c.is_card(AttackCard) and not c.is_card(DuelCard):
                return arg

            for tgt in tl:
                g.process_action(ExterminateAction(src, tgt))

        return arg


@register_eh
class ExterminateFadeHandler(EventHandler):
    interested = ('action_after', 'action_apply')

    def handle(self, evt_type, arg):
        if ((evt_type == 'action_after' and isinstance(arg, PlayerTurn)) or
            (evt_type == 'action_apply' and isinstance(arg, PlayerDeath) and arg.target.has_skill(Exterminate))):  # noqa

            g = Game.getgame()
            for p in g.players:
                if p.tags.pop('exterminate', ''):
                    p.reenable_skill('exterminate')

        return arg


@register_character_to('common')
class Flandre(Character):
    skills = [CriticalStrike, Exterminate]
    eventhandlers_required = [CriticalStrikeHandler, ExterminateHandler]
    maxlife = 4
