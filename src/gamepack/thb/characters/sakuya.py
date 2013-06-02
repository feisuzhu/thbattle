# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import ActionStage, FatetellStage, GenericAction
from ..cards import Skill, Attack, AttackCard, WearEquipmentAction, t_None, t_OtherOne


class FlyingKnife(Skill):
    associated_action = Attack
    target = t_OtherOne

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if not c.resides_in: return False
        if not c.resides_in.type in ('cards', 'showncards', 'equips'): return False
        act = c.associated_action
        if not (act and issubclass(act, WearEquipmentAction)): return False
        return True

    def is_card(self, cls):
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)


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
