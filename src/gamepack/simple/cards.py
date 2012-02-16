# -*- coding: utf-8 -*-
# Cards and Deck definition

from game.autoenv import Game, GameError
import random
import logging
log = logging.getLogger('SimpleGame_Cards')

class Card(object):
    name_lookup = dict(
        attack=u'杀',
        graze=u'闪',
        heal=u'药',
        hidden=u'BUG!!!',
    )
    import actions
    action_lookup = dict(
        attack = actions.Attack,
        heal = actions.Heal,
    )
    del actions
    def __init__(self, t):
        self.type = t
        self.name = self.name_lookup[t]
        self.associated_action = self.action_lookup.get(t)

        self.syncid = 0 # Deck will touch this

    def __data__(self):
        return dict(
            type=self.type,
            syncid=self.syncid,
        )

    def __eq__(self, other):
        if not type(self) == type(other): return False
        return self.syncid == other.syncid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 84065234 + self.syncid

    def sync(self, data):
        if data['syncid'] != self.syncid:
            raise GameError('Card: out of sync')
        t = data['type']
        self.type = t
        self.name = self.name_lookup[t]
        self.associated_action = self.action_lookup.get(t)

class Deck(object):
    def __init__(self):
        self.cards_record = {}

    def drawcards(self, num):
        g = Game.getgame()
        cards = []

        for i in xrange(num):
            if Game.SERVER_SIDE:
                c = Card((random.choice(['attack','graze', 'heal'])))
            elif Game.CLIENT_SIDE:
                c = Card('hidden')
            sid = g.get_synctag()
            c.syncid = sid
            cards.append(c)
            self.cards_record[sid] = c

        return cards

    def getcards(self, idlist):
        return [self.cards_record.get(cid) for cid in idlist]
