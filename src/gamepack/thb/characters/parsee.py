# -*- coding: utf-8 -*-
from game.autoenv import Game
from .baseclasses import Character, register_character
from ..actions import EventHandler, UserAction, migrate_cards, LaunchCard, user_choose_option
from ..cards import Card, TreatAsSkill, DemolitionCard, DummyCard, Demolition


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


class EnvyRecycleAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        card = self.card
        assert card.resides_in.owner is None
        migrate_cards([card], self.source.cards)
        return True


class EnvyRecycle(DummyCard):
    distance = 1


class EnvyHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, Demolition): return act
        if not act.associated_card.is_card(Envy): return act
        self.card = card = act.card

        if card.suit != Card.DIAMOND: return act

        src = act.source
        tgt = act.target

        dist = LaunchCard.calc_distance(src, EnvyRecycle())
        if not dist[tgt] <= 0: return act

        if not user_choose_option(self, src): return act

        g = Game.getgame()
        g.process_action(EnvyRecycleAction(src, tgt, card))

        return act

@register_character
class Parsee(Character):
    skills = [Envy]
    eventhandlers_required = [EnvyHandler]
    maxlife = 4
