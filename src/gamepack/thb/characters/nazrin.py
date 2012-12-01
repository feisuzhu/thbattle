# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class TreasureHunt(FatetellAction):
    def apply_action(self):
        tgt = self.target
        ft = Fatetell(tgt, lambda c: c.suit in (Card.SPADE, Card.CLUB))
        g = Game.getgame()
        if g.process_action(ft):
            self.card = c = ft.card
            migrate_cards([c], tgt.cards)
            tgt.need_shuffle = True
            return True
        return False

class TreasureHuntSkill(Skill):
    associated_action = None
    target = t_None

class TreasureHuntHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            tgt = act.target
            if not tgt.has_skill(TreasureHuntSkill): return act
            g = Game.getgame()
            while True:
                if not tgt.user_input('choose_option', self): return act
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
            cl[0].resides_in.type in ('handcard', 'showncard')
        )

@register_character
class Nazrin(Character):
    skills = [TreasureHuntSkill, Agile]
    eventhandlers_required = [TreasureHuntHandler]
    maxlife = 3
