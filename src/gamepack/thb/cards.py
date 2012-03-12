# -*- coding: utf-8 -*-
# Cards and Deck definition

from game.autoenv import Game, GameError
import random
import logging
log = logging.getLogger('SimpleGame_Cards')

import actions

class Card(object):
    card_classes = {}

    def __init__(self):
        self.syncid = 0 # Deck will touch this

    def __data__(self):
        return dict(
            type=self.__class__.__name__,
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

class Deck(object):
    def __init__(self):
        self.cards_record = {}

    def drawcards(self, num):
        g = Game.getgame()
        cards = []

        for i in xrange(num):
            if Game.SERVER_SIDE:
                c = random.choice(Card.card_classes.values())()
            elif Game.CLIENT_SIDE:
                c = HiddenCard()
            sid = g.get_synctag()
            c.syncid = sid
            cards.append(c)
            self.cards_record[sid] = c

        return cards

    def getcards(self, idlist):
        return [self.cards_record.get(cid) for cid in idlist]

class HiddenCard(Card): # special thing....
    associated_action = None
    target = None

def card_def(clsname, bases, _dict):
    cls = type(clsname, (Card,), _dict)
    for a in ('associated_action', 'target'):
        assert hasattr(cls, a)
    Card.card_classes[clsname] = cls
    return cls

__metaclass__ = card_def

# --------------------------------------------------

class AttackCard:
    associated_action = actions.Attack
    target = 1

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
