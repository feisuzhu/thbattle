# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import EventHandler, LaunchCard, UserAction, migrate_cards
from ..cards import Card, Demolition, DemolitionCard, DummyCard, Skill, TreatAs
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import Game, user_input


# -- code --
class Envy(TreatAs, Skill):
    treat_as = DemolitionCard
    skill_category = ('character', 'active')

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if c.resides_in is None: return False
        if c.resides_in.type not in ('cards', 'showncards', 'equips'): return False
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        return True


class EnvyRecycleAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        card = self.card
        assert not card.resides_in or card.resides_in.owner is None
        migrate_cards([card], self.source.cards, unwrap=True)
        return True


class EnvyRecycle(DummyCard):
    distance = 1


class EnvyHandler(EventHandler):
    interested = ('action_after',)
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, Demolition): return act
        if not act.associated_card.is_card(Envy): return act
        if not act.source.has_skill(Envy): return act

        src = act.source
        tgt = act.target
        self.card = card = act.card

        if src.dead: return act
        if card.suit != Card.DIAMOND: return act

        dist = LaunchCard.calc_distance(src, EnvyRecycle())
        if not dist[tgt] <= 0: return act

        if not user_input([src], ChooseOptionInputlet(self, (False, True))):
            return act

        g = Game.getgame()
        g.process_action(EnvyRecycleAction(src, tgt, card))

        return act


@register_character
class Parsee(Character):
    skills = [Envy]
    eventhandlers_required = [EnvyHandler]
    maxlife = 4
