# -*- coding: utf-8 -*-
# Cards and Deck definition

from game.autoenv import Game, GameError
import random
import logging
log = logging.getLogger('THBattle_Cards')

from utils import BatchList

import actions

class Card(object):
    NOTSET = 0
    SPADE = 1
    HEART = 2
    CLUB = 3
    DIAMOND = 4

    card_classes = {}

    def __init__(self, suit=NOTSET, number=0, resides_in=None):
        self.syncid = 0 # Deck will touch this
        self.suit = suit
        self.number = number
        self.resides_in = resides_in

    def __data__(self):
        return dict(
            type=self.__class__.__name__,
            suit=self.suit,
            number=self.number,
            syncid=self.syncid,
        )

    def __eq__(self, other):
        if not isinstance(other, Card): return False
        return self.syncid == other.syncid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 84065234 + self.syncid

    def sync(self, data):
        if data['syncid'] != self.syncid:
            raise GameError('Card: out of sync')
        clsname = data['type']
        cls = Card.card_classes.get(clsname)
        if not cls: raise GameError('Card: unknown card class')
        self.__class__ = cls
        self.suit = data['suit']
        self.number = data['number']

    def move_to(self, resides_in):
        if self.resides_in is not None:
            self.resides_in.remove(self)

        if resides_in is not None:
            resides_in.append(self)

        self.resides_in = resides_in

class CardList(BatchList):
    DECKCARD = 'deckcard'
    DROPPEDCARD = 'droppedcard'
    HANDCARD = 'handcard'
    SHOWNCARD = 'showncard'
    EQUIPS = 'equips'
    FATETELL = 'fatetell'
    def __init__(self, owner, type, arg):
        self.owner = owner
        self.type = type
        BatchList.__init__(self, arg)

    def __repr__(self):
        return "CardList(%s, %s, len([...]) == %d)" % (self.owner, self.type, len(self))

class Deck(object):
    def __init__(self):
        self.cards_record = {}
        self.droppedcards = CardList(None, CardList.DROPPEDCARD, [])
        cards = CardList(None, CardList.DECKCARD, [])
        self.cards = cards
        if Game.SERVER_SIDE:
            cards[:] = [cls(suit, n, cards) for cls, suit, n in card_definition]
            random.shuffle(cards)
        elif Game.CLIENT_SIDE:
            self.cards[:] = [HiddenCard(Card.NOTSET, 0, cards) for i in xrange(len(card_definition))]

    def getcards(self, num):
        g = Game.getgame()
        rst = []

        if len(self.cards) <= num:
            if Game.SERVER_SIDE:
                # performance hack
                random.shuffle(self.droppedcards)
                cards = self.cards
                for c in self.droppedcards:
                    c.resides_in = cards
                cards.extend(self.droppedcards)
            elif Game.CLIENT_SIDE:
                self.cards.extend([HiddenCard() for i in xrange(len(self.droppedcards))])

            self.droppedcards = []

        for i in xrange(num):
            c = self.cards[i]
            sid = g.get_synctag()
            c.syncid = sid
            rst.append(c)
            self.cards_record[sid] = c

        return rst

    def lookupcards(self, idlist):
        return [self.cards_record.get(cid) for cid in idlist]

class HiddenCard(Card): # special thing....
    associated_action = None
    target = None

def card_meta(clsname, bases, _dict):
    cls = type(clsname, (Card,), _dict)
    for a in ('associated_action', 'target'):
        assert hasattr(cls, a)
    Card.card_classes[clsname] = cls
    return cls

__metaclass__ = card_meta

# --------------------------------------------------

class AttackCard:
    associated_action = actions.Attack
    target = 1
    distance = 1

class GrazeCard:
    associated_action = None
    target = None

class HealCard:
    associated_action = actions.Heal
    target = 'self'

class DemolitionCard:
    associated_action = actions.Demolition
    target = 1

class RejectCard:
    associated_action = None
    target = None

class SealingArrayCard:
    associated_action = actions.SealingArray
    target = 1

class NazrinRodCard:
    associated_action = actions.NazrinRod
    target = 'self'

# --------------------------------------------------

__metaclass__ = type

card_definition = [
    (AttackCard, Card.SPADE, 1), (GrazeCard, Card.SPADE, 1), (HealCard, Card.SPADE, 1), (DemolitionCard, Card.SPADE, 1),
    (AttackCard, Card.SPADE, 2), (GrazeCard, Card.SPADE, 2), (HealCard, Card.SPADE, 2), (DemolitionCard, Card.SPADE, 2),
    (AttackCard, Card.SPADE, 3), (GrazeCard, Card.SPADE, 3), (HealCard, Card.SPADE, 3), (DemolitionCard, Card.SPADE, 3),
    (AttackCard, Card.SPADE, 4), (GrazeCard, Card.SPADE, 4), (HealCard, Card.SPADE, 4), (DemolitionCard, Card.SPADE, 4),
    (AttackCard, Card.SPADE, 5), (GrazeCard, Card.SPADE, 5), (HealCard, Card.SPADE, 5), (DemolitionCard, Card.SPADE, 5),
    (AttackCard, Card.SPADE, 6), (GrazeCard, Card.SPADE, 6), (HealCard, Card.SPADE, 6), (DemolitionCard, Card.SPADE, 6),
    (AttackCard, Card.SPADE, 7), (GrazeCard, Card.SPADE, 7), (HealCard, Card.SPADE, 7), (DemolitionCard, Card.SPADE, 7),
    (AttackCard, Card.SPADE, 8), (GrazeCard, Card.SPADE, 8), (HealCard, Card.SPADE, 8), (DemolitionCard, Card.SPADE, 8),
    (AttackCard, Card.SPADE, 9), (GrazeCard, Card.SPADE, 9), (HealCard, Card.SPADE, 9), (DemolitionCard, Card.SPADE, 9),
    (AttackCard, Card.SPADE, 10), (GrazeCard, Card.SPADE, 10), (HealCard, Card.SPADE, 10), (DemolitionCard, Card.SPADE, 10),
    (AttackCard, Card.SPADE, 11), (GrazeCard, Card.SPADE, 11), (HealCard, Card.SPADE, 11), (DemolitionCard, Card.SPADE, 11),
    (RejectCard, Card.SPADE, 12), (RejectCard, Card.SPADE, 12), (RejectCard, Card.SPADE, 12), (RejectCard, Card.SPADE, 12),
    (RejectCard, Card.SPADE, 13), (RejectCard, Card.SPADE, 13), (RejectCard, Card.SPADE, 13), (RejectCard, Card.SPADE, 13),

    (SealingArrayCard, Card.HEART, 1), (NazrinRodCard, Card.HEART, 1), (HealCard, Card.HEART, 1), (DemolitionCard, Card.HEART, 1),
    (SealingArrayCard, Card.HEART, 2), (NazrinRodCard, Card.HEART, 2), (HealCard, Card.HEART, 2), (DemolitionCard, Card.HEART, 2),
    (SealingArrayCard, Card.HEART, 3), (NazrinRodCard, Card.HEART, 3), (HealCard, Card.HEART, 3), (DemolitionCard, Card.HEART, 3),
    (SealingArrayCard, Card.HEART, 4), (NazrinRodCard, Card.HEART, 4), (HealCard, Card.HEART, 4), (DemolitionCard, Card.HEART, 4),
    (SealingArrayCard, Card.HEART, 5), (NazrinRodCard, Card.HEART, 5), (HealCard, Card.HEART, 5), (DemolitionCard, Card.HEART, 5),
    (SealingArrayCard, Card.HEART, 6), (NazrinRodCard, Card.HEART, 6), (HealCard, Card.HEART, 6), (DemolitionCard, Card.HEART, 6),
    (SealingArrayCard, Card.HEART, 7), (NazrinRodCard, Card.HEART, 7), (HealCard, Card.HEART, 7), (DemolitionCard, Card.HEART, 7),
    (SealingArrayCard, Card.HEART, 8), (NazrinRodCard, Card.HEART, 8), (HealCard, Card.HEART, 8), (DemolitionCard, Card.HEART, 8),
    (SealingArrayCard, Card.HEART, 9), (NazrinRodCard, Card.HEART, 9), (HealCard, Card.HEART, 9), (DemolitionCard, Card.HEART, 9),
    (SealingArrayCard, Card.HEART, 10), (NazrinRodCard, Card.HEART, 10), (HealCard, Card.HEART, 10), (DemolitionCard, Card.HEART, 10),
    (SealingArrayCard, Card.HEART, 11), (NazrinRodCard, Card.HEART, 11), (HealCard, Card.HEART, 11), (DemolitionCard, Card.HEART, 11),
    (RejectCard, Card.HEART, 12), (RejectCard, Card.HEART, 12), (RejectCard, Card.HEART, 12), (RejectCard, Card.HEART, 12),
    (RejectCard, Card.HEART, 13), (RejectCard, Card.HEART, 13), (RejectCard, Card.HEART, 13), (RejectCard, Card.HEART, 13),

    (AttackCard, Card.CLUB, 1), (GrazeCard, Card.CLUB, 1), (HealCard, Card.CLUB, 1), (DemolitionCard, Card.CLUB, 1),
    (AttackCard, Card.CLUB, 2), (GrazeCard, Card.CLUB, 2), (HealCard, Card.CLUB, 2), (DemolitionCard, Card.CLUB, 2),
    (AttackCard, Card.CLUB, 3), (GrazeCard, Card.CLUB, 3), (HealCard, Card.CLUB, 3), (DemolitionCard, Card.CLUB, 3),
    (AttackCard, Card.CLUB, 4), (GrazeCard, Card.CLUB, 4), (HealCard, Card.CLUB, 4), (DemolitionCard, Card.CLUB, 4),
    (AttackCard, Card.CLUB, 5), (GrazeCard, Card.CLUB, 5), (HealCard, Card.CLUB, 5), (DemolitionCard, Card.CLUB, 5),
    (AttackCard, Card.CLUB, 6), (GrazeCard, Card.CLUB, 6), (HealCard, Card.CLUB, 6), (DemolitionCard, Card.CLUB, 6),
    (AttackCard, Card.CLUB, 7), (GrazeCard, Card.CLUB, 7), (HealCard, Card.CLUB, 7), (DemolitionCard, Card.CLUB, 7),
    (AttackCard, Card.CLUB, 8), (GrazeCard, Card.CLUB, 8), (HealCard, Card.CLUB, 8), (DemolitionCard, Card.CLUB, 8),
    (AttackCard, Card.CLUB, 9), (GrazeCard, Card.CLUB, 9), (HealCard, Card.CLUB, 9), (DemolitionCard, Card.CLUB, 9),
    (AttackCard, Card.CLUB, 10), (GrazeCard, Card.CLUB, 10), (HealCard, Card.CLUB, 10), (DemolitionCard, Card.CLUB, 10),
    (AttackCard, Card.CLUB, 11), (GrazeCard, Card.CLUB, 11), (HealCard, Card.CLUB, 11), (DemolitionCard, Card.CLUB, 11),
    (RejectCard, Card.CLUB, 12), (RejectCard, Card.CLUB, 12), (RejectCard, Card.CLUB, 12), (RejectCard, Card.CLUB, 12),
    (RejectCard, Card.CLUB, 13), (RejectCard, Card.CLUB, 13), (RejectCard, Card.CLUB, 13), (RejectCard, Card.CLUB, 13),

    (AttackCard, Card.DIAMOND, 1), (GrazeCard, Card.DIAMOND, 1), (HealCard, Card.DIAMOND, 1), (DemolitionCard, Card.DIAMOND, 1),
    (AttackCard, Card.DIAMOND, 2), (GrazeCard, Card.DIAMOND, 2), (HealCard, Card.DIAMOND, 2), (DemolitionCard, Card.DIAMOND, 2),
    (AttackCard, Card.DIAMOND, 3), (GrazeCard, Card.DIAMOND, 3), (HealCard, Card.DIAMOND, 3), (DemolitionCard, Card.DIAMOND, 3),
    (AttackCard, Card.DIAMOND, 4), (GrazeCard, Card.DIAMOND, 4), (HealCard, Card.DIAMOND, 4), (DemolitionCard, Card.DIAMOND, 4),
    (AttackCard, Card.DIAMOND, 5), (GrazeCard, Card.DIAMOND, 5), (HealCard, Card.DIAMOND, 5), (DemolitionCard, Card.DIAMOND, 5),
    (AttackCard, Card.DIAMOND, 6), (GrazeCard, Card.DIAMOND, 6), (HealCard, Card.DIAMOND, 6), (DemolitionCard, Card.DIAMOND, 6),
    (AttackCard, Card.DIAMOND, 7), (GrazeCard, Card.DIAMOND, 7), (HealCard, Card.DIAMOND, 7), (DemolitionCard, Card.DIAMOND, 7),
    (AttackCard, Card.DIAMOND, 8), (GrazeCard, Card.DIAMOND, 8), (HealCard, Card.DIAMOND, 8), (DemolitionCard, Card.DIAMOND, 8),
    (AttackCard, Card.DIAMOND, 9), (GrazeCard, Card.DIAMOND, 9), (HealCard, Card.DIAMOND, 9), (DemolitionCard, Card.DIAMOND, 9),
    (AttackCard, Card.DIAMOND, 10), (GrazeCard, Card.DIAMOND, 10), (HealCard, Card.DIAMOND, 10), (DemolitionCard, Card.DIAMOND, 10),
    (AttackCard, Card.DIAMOND, 11), (GrazeCard, Card.DIAMOND, 11), (HealCard, Card.DIAMOND, 11), (DemolitionCard, Card.DIAMOND, 11),
    (RejectCard, Card.DIAMOND, 12), (RejectCard, Card.DIAMOND, 12), (RejectCard, Card.DIAMOND, 12), (RejectCard, Card.DIAMOND, 12),
    (RejectCard, Card.DIAMOND, 13), (RejectCard, Card.DIAMOND, 13), (RejectCard, Card.DIAMOND, 13), (RejectCard, Card.DIAMOND, 13),
]
