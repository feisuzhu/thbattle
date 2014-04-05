# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import FatetellAction, Fatetell, FatetellStage, migrate_cards
from ..cards import Card, Skill, TreatAsSkill, GrazeCard, t_None
from ..inputlets import ChooseOptionInputlet


class TreasureHunt(FatetellAction):
    def apply_action(self):
        tgt = self.target
        ft = Fatetell(tgt, lambda c: c.suit in (Card.SPADE, Card.CLUB))
        g = Game.getgame()
        if g.process_action(ft):
            self.card = c = ft.card
            migrate_cards([c], tgt.cards)
            return True

        return False


class TreasureHuntSkill(Skill):
    associated_action = None
    target = t_None


class TreasureHuntHandler(EventHandler):
    execute_before = ('CiguateraHandler', )
    
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            tgt = act.target
            if not tgt.has_skill(TreasureHuntSkill): return act
            g = Game.getgame()
            while True:
                if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                    return act
                if not g.process_action(TreasureHunt(tgt, tgt)):
                    return act
        return act


class Agile(TreatAsSkill):
    treat_as = GrazeCard

    def check(self):
        cl = self.associated_cards
        return (
            cl and len(cl) == 1 and
            cl[0].suit in (Card.SPADE, Card.CLUB) and
            cl[0].resides_in.type in ('cards', 'showncards')
        )


@register_character
class Nazrin(Character):
    skills = [TreasureHuntSkill, Agile]
    eventhandlers_required = [TreasureHuntHandler]
    maxlife = 3
