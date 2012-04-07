# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..skill import *
from ..cards import *

class CriticalStrike(Skill):
    associated_action = None
    target = t_None

class CriticalStrikeHandler(EventHandler):
    execute_after = (AttackCardHandler, )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if not tgt.has_skill(CriticalStrike): return act
            if not tgt.user_input('choose_option', self): return act

            tgt.tags['attack_num'] += 1
            tgt.tags['flan_cs'] = tgt.tags['turn_count']
            tgt.tags['flan_lasttarget'] = None
            act.amount = max(0, act.amount - 1)
            
        elif evt_type == 'action_before' and isinstance(act, BaseAttack):
            src = act.source
            st = src.tags
            if not st.get('flan_cs', 0) == st.get('turn_count'): return act
            if not src.has_skill(CriticalStrike): return act
            tgt = act.target
            st['flan_lasttarget'] = tgt
            act.damage += 1
        elif evt_type == 'action_can_fire':
            a, valid = act
            if not isinstance(a, LaunchCard): return act
            src = a.source
            st = src.tags
            if not st.get('flan_cs', 0) == st.get('turn_count'): return act
            if not src.has_skill(CriticalStrike): return act
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
