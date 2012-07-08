# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class CriticalStrike(Skill):
    associated_action = None
    target = t_None

class CriticalStrikeAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        tgt.tags['attack_num'] = 10000
        tgt.tags['flan_cs'] = True
        tgt.tags['flan_lasttarget'] = None
        return True

class CriticalStrikeHandler(EventHandler):
    execute_after = ('AttackCardHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if not tgt.has_skill(CriticalStrike): return act
            if not tgt.user_input('choose_option', self): return act

            Game.getgame().process_action(CriticalStrikeAction(tgt, tgt))

            act.amount = max(0, act.amount - 1)

        elif evt_type == 'action_after' and isinstance(act, ActionStage):
            src = act.actor
            if not src.has_skill(CriticalStrike): return act
            st = src.tags
            st['flan_lasttarget'] = None
            st['flan_cs'] = False

        elif evt_type == 'action_apply' and isinstance(act, (BaseAttack, BaseDuel)):
            src = act.source
            st = src.tags
            if not st['flan_cs']: return act
            if not Game.getgame().current_turn is src: return act
            if not src.has_skill(CriticalStrike): return act
            tgt = act.target
            if isinstance(act, BaseAttack):
                st['flan_lasttarget'] = tgt
                act.damage += 1
            elif isinstance(act, BaseDuel):
                act.source_damage += 1

        elif evt_type == 'action_can_fire':
            a, valid = act
            if not isinstance(a, LaunchCard): return act
            src = a.source
            st = src.tags
            if not st['flan_cs']: return act
            if not src.has_skill(CriticalStrike): return act
            if not a.card.is_card(AttackCard): return act
            last = st['flan_lasttarget']
            tl = a.target_list
            if last in tl:
                return (a, False)

        return act

@register_character
class Flandre(Character):
    skills = [CriticalStrike]
    eventhandlers_required = [CriticalStrikeHandler]
    maxlife = 4
