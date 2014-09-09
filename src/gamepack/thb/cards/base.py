# -*- coding: utf-8 -*-
# Cards and Deck classes

from collections import deque
from ..common import get_seed_for
from game.autoenv import Game, GameError, GameObject
from weakref import WeakValueDictionary
import logging
import random

log = logging.getLogger('THBattle_Cards')


class Card(GameObject):
    NOTSET = 0
    SPADE = 1
    HEART = 2
    CLUB = 3
    DIAMOND = 4

    RED = 5
    BLACK = 6

    SUIT_REV = {
        0: '?',
        1: 'SPADE', 2: 'HEART',
        3: 'CLUB', 4: 'DIAMOND',
    }

    NUM_REV = {
        0: '?', 1: 'A', 2: '2', 3: '3', 4: '4',
        5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
        10: '10', 11: 'J', 12: 'Q', 13: 'K',
    }

    _color = None
    card_classes = {}
    usage = 'launch'

    def __init__(self, suit=NOTSET, number=0, resides_in=None):
        self.syncid = 0  # Deck will touch this
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

    def sync(self, data):  # this only executes at client side, let it crash.
        if data['syncid'] != self.syncid:
            logging.error(
                'CardOOS: server: %s, %d, %d, syncid=%d; client: %s, %d, %d, syncid=%d',

                data['type'],
                self.SUIT_REV.get(data['suit'], data['suit']),
                self.NUM_REV.get(data['number'], data['number']),
                data['syncid'],

                self.__class__.__name__,
                self.SUIT_REV.get(self.suit),
                self.NUM_REV.get(self.number),
                self.syncid,
            )
            raise GameError('Card: out of sync')

        clsname = data['type']
        cls = Card.card_classes.get(clsname)
        if not cls: raise GameError('Card: unknown card class')
        self.__class__ = cls
        self.suit = data['suit']
        self.number = data['number']

    def move_to(self, resides_in):
        self.detach()
        if resides_in is not None:
            resides_in.append(self)

        self.resides_in = resides_in

    def detach(self):
        try:
            self.resides_in.remove(self)
        except (AttributeError, ValueError):
            pass

    def attach(self):
        if self not in self.resides_in:
            self.resides_in.append(self)

    @property
    def detached(self):
        return self.resides_in is not None and self not in self.resides_in

    def __repr__(self):
        return u"{name}({suit}, {num}{detached})".format(
            name=self.__class__.__name__,
            suit=self.SUIT_REV.get(self.suit, self.suit),
            num=self. NUM_REV.get(self.number, self.number),
            detached=u', detached' if self.detached else u''
        )

    def is_card(self, cls):
        return isinstance(self, cls)

    @property
    def color(self):
        if self._color is not None: return self._color
        s = self.suit
        if s in (Card.HEART, Card.DIAMOND):
            return Card.RED
        elif s in (Card.SPADE, Card.CLUB):
            return Card.BLACK
        else:
            return Card.NOTSET

    @color.setter
    def color(self, val):
        self._color = val


class VirtualCard(Card):
    __eq__ = object.__eq__
    __ne__ = object.__ne__
    __hash__ = object.__hash__

    sort_index = 0
    syncid = 0
    usage = 'none'

    def __init__(self, player):
        self.player           = player
        self.suit             = Card.NOTSET
        self.number           = 0
        self.associated_cards = []
        self.resides_in       = player.cards
        self.action_params    = {}

    def __data__(self):
        return {
            'class':  self.__class__.__name__,
            'syncid': self.syncid,
            'vcard':  True,
            'params': self.action_params,
        }

    def check(self):  # override this
        return False

    @classmethod
    def unwrap(cls, vcards):
        l = []
        sl = vcards[:]

        while sl:
            s = sl.pop()
            try:
                sl.extend(s.associated_cards)
            except AttributeError:
                l.append(s)

        return l

    @classmethod
    def wrap(cls, cl, player, params=None):
        vc = cls(player)
        vc.action_params = params or {}

        if not cl:
            vc.associated_cards = []
            return vc

        suit = cl[0].suit if len(cl) == 1 else Card.NOTSET

        color = set([c.color for c in cl])
        color = color.pop() if len(color) == 1 else Card.NOTSET

        num = set([c.number for c in cl])
        num = num.pop() if len(num) == 1 else Card.NOTSET

        vc.suit, vc.number, vc.color = suit, num, color
        vc.associated_cards = cl[:]
        return vc

    def sync(self, data):
        assert data['vcard']
        assert self.__class__.__name__ == data['class']
        assert self.syncid == data['syncid']
        assert self.action_params == data['params']


class CardList(GameObject, deque):
    DECKCARD = 'deckcard'
    DROPPEDCARD = 'droppedcard'
    CARDS = 'cards'
    SHOWNCARDS = 'showncards'
    EQUIPS = 'equips'
    FATETELL = 'fatetell'
    SPECIAL = 'special'
    FAITHS = 'faiths'

    def __init__(self, owner, type):
        self.owner = owner
        self.type = type
        deque.__init__(self)

    def __repr__(self):
        return "CardList(owner=%s, type=%s, len == %d)" % (self.owner, self.type, len(self))


class Deck(GameObject):
    def __init__(self, card_definition=None):
        if not card_definition:
            from .definition import card_definition

        self.cards_record = {}
        self.vcards_record = WeakValueDictionary()
        self.droppedcards = CardList(None, 'droppedcard')
        self.disputed = CardList(None, 'disputed')
        cards = CardList(None, 'deckcard')
        self.cards = cards
        cards.extend(
            cls(suit, n, cards)
            for cls, suit, n in card_definition
        )
        self.shuffle(cards)

    def getcards(self, num):
        cl = self.cards
        if len(self.cards) <= num:
            dcl = self.droppedcards

            assert all(not c.is_card(VirtualCard) for c in dcl)
            dropped = list(dcl)

            dcl.clear()
            dcl.extend(dropped[-10:])

            tmpcl = CardList(None, 'temp')
            l = [c.__class__(c.suit, c.number, cl) for c in dropped[:-10]]
            tmpcl.extend(l)
            self.shuffle(tmpcl)
            cl.extend(tmpcl)

        cl = self.cards
        rst = []
        for i in xrange(min(len(cl), num)):
            rst.append(cl[i])

        return rst

    def lookupcards(self, idlist):
        l = []
        cr = self.cards_record
        vcr = self.vcards_record
        for cid in idlist:
            c = vcr.get(cid, None) or cr.get(cid, None)
            c and l.append(c)

        return l

    def register_card(self, card):
        assert not card.syncid
        sid = Game.getgame().get_synctag()
        card.syncid = sid
        self.cards_record[sid] = card
        return sid

    def register_vcard(self, vc):
        sid = Game.getgame().get_synctag()
        vc.syncid = sid
        self.vcards_record[sid] = vc
        return sid

    def shuffle(self, cl):
        owner = cl.owner
        seed = get_seed_for(owner)

        if seed:  # cardlist owner & server
            shuffler = random.Random(seed)
            shuffler.shuffle(cl)
        else:  # others
            for c in cl:
                c.__class__ = HiddenCard
                c.suit = c.number = 0

        for c in cl:
            c.syncid = 0
            self.register_card(c)


class Skill(VirtualCard):
    category = ('skill', )

    def __init__(self, player):
        assert player is not None
        VirtualCard.__init__(self, player)

    def check(self):  # override this
        return False

    # target = xxx
    # associated_action = xxx
    # instance var: associated_cards = xxx


class TreatAs(object):
    treat_as = None  # can't be VirtualCard here
    usage = 'launch'

    @property
    def category(self):
        return ('skill', 'treat_as') + self.treat_as.category

    def check(self):
        return False

    def is_card(self, cls):
        if issubclass(self.treat_as, cls): return True
        return isinstance(self, cls)

    def __getattr__(self, name):
        return getattr(self.treat_as, name)


# card targets:
@staticmethod
def t_None(g, source, tl):
    return (None, False)


@staticmethod
def t_Self(g, source, tl):
    return ([source], True)


@staticmethod
def t_OtherOne(g, source, tl):
    tl = [t for t in tl if not t.dead]
    try:
        tl.remove(source)
    except ValueError:
        pass
    return (tl[-1:], bool(len(tl)))


@staticmethod
def t_One(g, source, tl):
    tl = [t for t in tl if not t.dead]
    return (tl[-1:], bool(len(tl)))


@staticmethod
def t_All(g, source, tl):
    l = g.players.rotate_to(source)
    del l[0]
    return ([t for t in l if not t.dead], True)


@staticmethod
def t_AllInclusive(g, source, tl):
    l = g.players.rotate_to(source)
    return ([t for t in l if not t.dead], True)


def t_OtherLessEqThanN(n):
    @staticmethod
    def _t_OtherLessEqThanN(g, source, tl):
        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(source)
        except ValueError:
            pass
        return (tl[:n], bool(len(tl)))
    return _t_OtherLessEqThanN


@staticmethod
def t_OneOrNone(g, source, tl):
    tl = [t for t in tl if not t.dead]
    return (tl[-1:], True)


def t_OtherN(n):
    @staticmethod
    def _t_OtherN(g, source, tl):
        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(source)
        except ValueError:
            pass
        return (tl[:n], bool(len(tl) >= n))
    return _t_OtherN


class HiddenCard(Card):  # special thing....
    associated_action = None
    target = t_None
