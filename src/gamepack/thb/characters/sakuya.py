# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *


class FlyingKnife(Skill):
    associated_action = Attack
    target = t_OtherOne
    def check(self):
        p = self.player
        if Game.getgame().current_turn is not p: return False
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if not c.resides_in: return False
        if not c.resides_in.type in (CardList.HANDCARD, CardList.SHOWNCARD, CardList.EQUIPS): return False
        if not issubclass(c.associated_action, WearEquipmentAction): return False
        return True


class LunaClockActionStage(ActionStage):
    def apply_action(self):
        rst = ActionStage.apply_action(self)
        tgt = self.target
        tgt.tags['turn_count'] += 1
        return rst


class LunaClock(Skill):
    associated_action = None
    target = t_None


class LunaClockHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            src = act.target
            if not src.has_skill(LunaClock): return act
            Game.getgame().process_action(LunaClockActionStage(src))
        return act

@register_character
class Sakuya(Character):
    skills = [FlyingKnife, LunaClock]
    eventhandlers_required = [LunaClockHandler]
    maxlife = 4
