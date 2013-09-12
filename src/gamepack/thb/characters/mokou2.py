# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, FatetellStage, DrawCardStage, DropCards, DrawCards, LifeLost, PlayerTurn
from ..actions import user_choose_cards, ask_for_action
from ..cards import Card, Skill, t_None
from ..cards.basic import Heal
from ..inputlets import ChooseOptionInputlet


class Ashes(Skill):
    associated_action = None
    target = t_None

class Reborn(Skill):
    associated_action = None
    target = t_None

class AshesAction(UserAction):
    def __init__(self, target):
        self.source = self.target = target

    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        g.process_action(LifeLost(tgt, tgt))
        g.process_action(DrawCards(tgt))
        return True

class RebornAction(UserAction):
    def __init__(self, target):
        self.source = self.target = target

    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        g.process_action(Heal(tgt, tgt))
        tgt.tags['reborn'] = True
        return True

class AshesHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.dead or not tgt.has_skill(Ashes): return act
            if len(tgt.cards) + len(tgt.showncards) >= tgt.life: return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(AshesAction(tgt))

        return act


class RebornHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            self.target = tgt = act.target
            if not tgt.has_skill(Reborn): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act
            
            if Game.getgame().process_action(RebornAction(tgt)):
                act.cancelled = True

        elif evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if tgt.tags.get('reborn'):
                del tgt.tags['reborn']
                act.cancelled = True

        return act

@register_character
class Mokou(Character):
    skills = [Reborn, Ashes]
    eventhandlers_required = [
        AshesHandler,
        RebornHandler
    ]
    maxlife = 4
