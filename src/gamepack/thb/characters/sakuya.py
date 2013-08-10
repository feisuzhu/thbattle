# -*- coding: utf-8 -*-

from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import ActionStage, FatetellStage, GenericAction
from ..cards import Skill, AttackCard, WearEquipmentAction, TreatAsSkill, t_None


class FlyingKnife(TreatAsSkill):
    treat_as = AttackCard
    distance = 99999

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if c.resides_in is None: return False
        if not c.resides_in.type in ('cards', 'showncards', 'equips'): return False
        act = c.associated_action
        if not (act and issubclass(act, WearEquipmentAction)): return False
        return True


class LunaClockActionStage(GenericAction):
    def apply_action(self):
        tags = self.target.tags
        tags['lunaclock'] = True
        Game.getgame().process_action(ActionStage(self.target))
        tags['lunaclock'] = False
        tags['turn_count'] += 1
        return True


class LunaClock(Skill):
    associated_action = None
    target = t_None


class LunaClockHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            src = act.target
            if not src.has_skill(LunaClock): return act
            Game.getgame().process_action(LunaClockActionStage(src, src))
        return act


@register_character
class Sakuya(Character):
    skills = [FlyingKnife, LunaClock]
    eventhandlers_required = [LunaClockHandler]
    maxlife = 4
