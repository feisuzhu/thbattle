# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import DropCards, LaunchCard, migrate_cards
from thb.cards.base import Card, Skill, DummyCard
from thb.cards.classes import Demolition, DemolitionCard, TreatAs
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler
from utils.misc import classmix


# -- code --
class Envy(TreatAs, Skill):
    treat_as = DemolitionCard
    skill_category = ['character', 'active']

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if c.resides_in is None: return False
        if c.resides_in.type not in ('cards', 'showncards', 'equips'): return False
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        return True


class EnvyRecycleAction(object):
    def apply_action(self):
        migrate_cards(self.cards, self.source.cards, unwrap=True)
        return True


class EnvyRecycle(DummyCard):
    distance = 1


class EnvyHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, DropCards): return act

        g = self.game
        pact = g.action_stack[-1]
        if not isinstance(pact, Demolition): return act
        if not pact.source.has_skill(Envy): return act

        src = pact.source
        tgt = pact.target
        self.card = card = pact.card

        assert len(act.cards) == 1
        assert card is act.cards[0]

        if card.resides_in is None:
            return act

        if card.resides_in.type not in ('cards', 'showncards', 'equips'):
            return act

        assert tgt is card.resides_in.owner

        if src.dead: return act
        if card.suit != Card.DIAMOND: return act

        dist = LaunchCard.calc_distance(src, EnvyRecycle())
        if not dist[tgt] <= 0: return act

        g.emit_event('ui_show_disputed', [card])

        if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
            return act

        act.__class__ = classmix(EnvyRecycleAction, act.__class__)
        return act


@register_character_to('common')
class Parsee(Character):
    skills = [Envy]
    eventhandlers = [EnvyHandler]
    maxlife = 4
