# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import ActionStageLaunchCard, Damage, DrawCardStage, GenericAction, PlayerDeath
from thb.actions import PlayerTurn, register_eh, ttags
from thb.cards.base import Skill
from thb.cards.classes import ActionLimitExceeded, AttackCard, AttackCardVitalityHandler, BaseAttack
from thb.cards.classes import BaseDuel, DuelCard, ElementalReactorSkill, UserAction, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class CriticalStrike(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class CriticalStrikeAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        ttags(tgt)['flan_cs'] = True
        tgt.tags['flan_targets'] = []
        return True


class CriticalStrikeLimit(ActionLimitExceeded):
    pass


class CriticalStrikeHandler(THBEventHandler):
    interested = ['action_apply', 'action_before', 'action_shootdown', 'action_stage_action']
    execute_after = [
        'AttackCardHandler',
        'FrozenFrogHandler',
        'ElementalReactorHandler',
        'ReversedScalesHandler',
    ]
    execute_before = [
        'MomijiShieldHandler',
        'WineHandler',
    ]

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if not tgt.has_skill(CriticalStrike): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            self.game.process_action(CriticalStrikeAction(tgt, tgt))

            act.amount = max(0, act.amount - 1)

        elif evt_type == 'action_apply' and isinstance(act, BaseAttack):
            src = act.source
            tags = src.tags
            if not self.in_critical_strike(src):
                return act

            tgt = act.target
            if isinstance(act, BaseAttack):
                tags['flan_targets'].append(tgt)
                act.damage += 1

        elif evt_type == 'action_before' and isinstance(act, Damage):
            g = self.game
            pact = g.action_stack[-1]
            if not isinstance(pact, BaseDuel):
                return act

            src, tgt = act.source, act.target

            if not self.in_critical_strike(src):
                return act

            act.amount += 1

        elif evt_type == 'action_before' and isinstance(act, ActionStageLaunchCard):
            src = act.source
            if not self.in_critical_strike(src):
                return act

            if act.card.is_card(AttackCard):
                act._[self.__class__] = 'vitality-consumed'
                src.tags['vitality'] -= 1

        elif evt_type == 'action_shootdown':
            if not isinstance(act, ActionStageLaunchCard): return act
            c = act.card
            src = act.source
            tags = src.tags
            if not self.in_critical_strike(src): return act
            if not c.is_card(AttackCard): return act
            if src.has_skill(ElementalReactorSkill): return act
            if src.tags['vitality'] > 0: return act
            if act._[self.__class__]: return act
            if set(act.target_list) & set(tags['flan_targets']):
                raise CriticalStrikeLimit

            return act

        elif evt_type == 'action_stage_action':
            tgt = act
            if not self.in_critical_strike(tgt): return act
            AttackCardVitalityHandler.disable(tgt)

        return act

    def in_critical_strike(self, p):
        return (
            ttags(p)['flan_cs'] and
            self.game.current_player is p and
            p.has_skill(CriticalStrike)
        )


class Exterminate(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class ExterminateAction(UserAction):

    def apply_action(self):
        tgt = self.target
        tgt.tags['exterminate'] = True
        for s in tgt.skills:
            if 'character' in s.skill_category:
                tgt.disable_skill(s, 'exterminate')

        return True


class ExterminateHandler(THBEventHandler):
    interested = ['choose_target']

    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            act, tl = arg
            src = act.source
            g = self.game

            if not src.has_skill(Exterminate):
                return arg

            c = act.card
            if not c.is_card(AttackCard) and not c.is_card(DuelCard):
                return arg

            for tgt in tl:
                g.process_action(ExterminateAction(src, tgt))

        return arg


@register_eh
class ExterminateFadeHandler(THBEventHandler):
    interested = ['action_after', 'action_apply']

    def handle(self, evt_type, arg):
        if ((evt_type == 'action_after' and isinstance(arg, PlayerTurn)) or
            (evt_type == 'action_apply' and isinstance(arg, PlayerDeath) and arg.target.has_skill(Exterminate))):  # noqa

            g = self.game()
            for p in g.players:
                if p.tags.pop('exterminate', ''):
                    p.reenable_skill('exterminate')

        return arg


@register_character_to('common')
class Flandre(Character):
    skills = [CriticalStrike, Exterminate]
    eventhandlers = [CriticalStrikeHandler, ExterminateHandler]
    maxlife = 4
