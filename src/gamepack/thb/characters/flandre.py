# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import GenericAction, ActionStageLaunchCard, DrawCardStage
from ..cards import ElementalReactorSkill, AttackCard, AttackCardHandler, BaseAttack, BaseDuel, Skill, t_None
from ..inputlets import ChooseOptionInputlet


class CriticalStrike(Skill):
    associated_action = None
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

        elif evt_type == 'action_apply' and isinstance(act, (BaseAttack, BaseDuel)):
            src = act.source
            st = src.tags
            if not st['flan_cs'] >= st['turn_count']: return act
            if not Game.getgame().current_turn is src: return act
            if not src.has_skill(CriticalStrike): return act
            tgt = act.target
            if isinstance(act, BaseAttack):
                st['flan_targets'].append(tgt)
                act.damage += 1
            elif isinstance(act, BaseDuel):
                act.source_damage += 1

        elif evt_type == 'action_can_fire':
            arg = act
            act, valid = arg
            if not isinstance(act, ActionStageLaunchCard): return arg
            c = act.card
            src = act.source
            tags = src.tags
            if not src.has_skill(CriticalStrike): return arg
            if not tags['flan_cs'] >= tags['turn_count']: return arg
            if not c.is_card(AttackCard): return arg
            if src.has_skill(ElementalReactorSkill): return arg
            if set(act.target_list) & set(tags['flan_targets']):
                return (act, False)

            return arg

        elif evt_type == 'action_stage_action':
            tgt = act
            tags = tgt.tags
            if not tgt.has_skill(CriticalStrike): return act
            if not tags['flan_cs'] >= tags['turn_count']: return act
            AttackCardHandler.set_freeattack(tgt)

        return act


@register_character
class Flandre(Character):
    skills = [CriticalStrike]
    eventhandlers_required = [CriticalStrikeHandler]
    maxlife = 4
