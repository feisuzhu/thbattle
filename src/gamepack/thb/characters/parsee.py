# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Envy(TreatAsSkill):
    treat_as = DemolitionCard
    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if not c.resides_in: return False
        if not c.resides_in.type in ('handcard', 'showncard', 'equips'): return False
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        return True


class EnvyAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        card = self.card
        assert card.resides_in.owner is self.target
        migrate_cards([card], self.source.cards)
        return True


class EnvyHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Demolition):
            src = act.source
            if src.has_skill(Envy):
                act.__class__ = classmix(act.__class__, Envy)
                act.retrieve = False

        elif evt_type == 'action_before' and isinstance(act, DropCards):
            g = Game.getgame()
            pact = g.action_stack[-1]
            if isinstance(pact, Envy):
                src = pact.source
                if pact.card.suit == Card.DIAMOND:
                    act.cancelled = True  # replace DropCards action
                    pact.retrieve = True

        elif evt_type == 'action_after' and isinstance(act, Envy):
            assert isinstance(act, Demolition)
            if act.retrieve:
                g = Game.getgame()
                g.process_action(EnvyAction(act.source, act.target, act.card))

        return act

@register_character
class Parsee(Character):
    skills = [Envy]
    eventhandlers_required = [EnvyHandler]
    maxlife = 4
