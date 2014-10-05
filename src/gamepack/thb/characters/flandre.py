# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import ActionStageLaunchCard, Damage, DrawCardStage, GenericAction
from ..cards import AttackCard, AttackCardHandler, BaseAttack, BaseDuel, ElementalReactorSkill
from ..cards import Skill, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class CriticalStrike(Skill):
    associated_action = None
    skill_category = ('character', 'active')
    target = t_None


class CriticalStrikeAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        tgt.tags['flan_cs'] = tgt.tags['turn_count']
        tgt.tags['flan_targets'] = []
        return True


class CriticalStrikeHandler(EventHandler):
    execute_after = (
        'AttackCardHandler',
        'FrozenFrogHandler',
        'ElementalReactorHandler',
        'ReversedScalesHandler',
    )
    execute_before = (
        'MomijiShieldHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if not tgt.has_skill(CriticalStrike): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(CriticalStrikeAction(tgt, tgt))

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
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, BaseDuel):
                return act

            src, tgt = act.source, act.target

            if not self.in_critical_strike(src):
                return act

            act.amount += 1

        elif evt_type == 'action_can_fire':
            arg = act
            act, valid = arg
            if not isinstance(act, ActionStageLaunchCard): return arg
            c = act.card
            src = act.source
            tags = src.tags
            if not self.in_critical_strike(src): return arg
            if not c.is_card(AttackCard): return arg
            if src.has_skill(ElementalReactorSkill): return arg
            if set(act.target_list) & set(tags['flan_targets']):
                return (act, False)

            return arg

        elif evt_type == 'action_stage_action':
            tgt = act
            if not self.in_critical_strike(tgt): return act
            AttackCardHandler.set_freeattack(tgt)

        return act

    def in_critical_strike(self, p):
        tags = p.tags
        return (
            tags['flan_cs'] >= tags['turn_count'] and
            Game.getgame().current_turn is p and
            p.has_skill(CriticalStrike)
        )


@register_character
class Flandre(Character):
    skills = [CriticalStrike]
    eventhandlers_required = [CriticalStrikeHandler]
    maxlife = 4
