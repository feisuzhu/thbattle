# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class CriticalStrike(FreeAttackSkill):
    associated_action = None
    target = t_None
    @staticmethod
    def is_valid(src, tl):
        st = src.tags
        if not st['flan_cs']: return False
        if tl & st['flan_targets']: return False
        return True

class CriticalStrikeAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        tgt.tags['attack_num'] = 10000
        tgt.tags['flan_cs'] = True
        tgt.tags['flan_targets'] = []
        return True


class CriticalStrikeHandler(EventHandler):
    execute_after = ('AttackCardHandler', 'FrozenFrogHandler')
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if not tgt.has_skill(CriticalStrike): return act
            if not user_choose_option(self, tgt): return act

            Game.getgame().process_action(CriticalStrikeAction(tgt, tgt))

            act.amount = max(0, act.amount - 1)

        elif (
            evt_type == 'action_after' and isinstance(act, ActionStage)
        ) or (
            evt_type == 'action_apply' and isinstance(act, PlayerTurn)
        ):
            src = act.target
            if not src.has_skill(CriticalStrike): return act
            st = src.tags
            st['flan_targets'] = []
            st['flan_cs'] = False

        elif evt_type == 'action_apply' and isinstance(act, (BaseAttack, BaseDuel)):
            src = act.source
            st = src.tags
            if not st['flan_cs']: return act
            if not Game.getgame().current_turn is src: return act
            if not src.has_skill(CriticalStrike): return act
            tgt = act.target
            if isinstance(act, BaseAttack):
                st['flan_targets'].append(tgt)
                act.damage += 1
            elif isinstance(act, BaseDuel):
                act.source_damage += 1

        return act


@register_character
class Flandre(Character):
    skills = [CriticalStrike]
    eventhandlers_required = [CriticalStrikeHandler]
    maxlife = 4
