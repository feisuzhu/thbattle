# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, FatetellStage, DropCards, DrawCards, LifeLost, PlayerTurn
from ..actions import user_choose_cards
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
        return True


class AshesHandler(EventHandler):
    execute_before = ('CiguateraHandler', )
    
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.dead or not tgt.has_skill(Ashes): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(AshesAction(tgt))

        return act


class RebornHandler(EventHandler):
    execute_before = ('CiguateraHandler', )
    card_usage = 'drop'
    
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            self.target = tgt = act.target
            if not tgt.has_skill(Reborn): return act
            cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
            if cards:
                g = Game.getgame()
                g.process_action(DropCards(tgt, cards))
                g.process_action(RebornAction(tgt))

        return act

    def cond(self, cards):
        if len(cards) != self.target.life: return False

        for card in cards:
            if card.color != Card.RED: return False

            if not card.resides_in.type in ('cards', 'showncards', 'equips'):
                return False

            if not bool(set(card.category) & {'basic', 'equipment'}):
                return False

        return True


@register_character
class Mokou(Character):
    skills = [Reborn, Ashes]
    eventhandlers_required = [AshesHandler, RebornHandler]
    maxlife = 4
