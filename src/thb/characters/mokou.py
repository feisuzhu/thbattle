# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import DrawCards, DropCards, FatetellStage, LifeLost, PlayerTurn, UserAction
from thb.actions import user_choose_cards
from thb.cards import Card, Skill, t_None
from thb.cards.basic import Heal
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class Ashes(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class Reborn(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
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
    interested = ('action_after',)
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
    interested = ('action_before',)
    execute_before = ('CiguateraHandler', )
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            self.target = tgt = act.target
            if not tgt.has_skill(Reborn): return act
            cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
            if cards:
                g = Game.getgame()
                g.process_action(DropCards(tgt, tgt, cards))
                if not tgt.dead: # Ensure no ui action_effect_after (str | se) after drop Exinwan causing fall
                    g.process_action(RebornAction(tgt))

        return act

    def cond(self, cards):
        if len(cards) != self.target.life:
            return False

        for card in cards:
            if card.color != Card.RED or card.is_card(Skill):
                return False

            if card.resides_in.type not in ('cards', 'showncards', 'equips'):
                return False

        return True


@register_character_to('common')
class Mokou(Character):
    skills = [Reborn, Ashes]
    eventhandlers_required = [AshesHandler, RebornHandler]
    maxlife = 4
