# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import deque
from weakref import WeakValueDictionary
import itertools
import logging

# -- third party --
# -- own --
from game.autoenv import Game, GameError, GameObject, list_shuffle


# -- code --
log = logging.getLogger('THBattle_Cards')
alloc_id = itertools.count(1).next


class Card(GameObject):
    NOTSET  = 0
    SPADE   = 1
    HEART   = 2
    CLUB    = 3
    DIAMOND = 4

    RED   = 5
    BLACK = 6

    SUIT_REV = {
        0: '?',
        1: 'SPADE', 2: 'HEART',
        3: 'CLUB',  4: 'DIAMOND',
    }

    NUM_REV = {
        0:  '?',  1:  'A', 2:  '2', 3:  '3', 4: '4',
        5:  '5',  6:  '6', 7:  '7', 8:  '8', 9: '9',
        10: '10', 11: 'J', 12: 'Q', 13: 'K',
    }

    _color = None
    card_classes = {}
    usage = 'launch'

    # True means this card's associated cards have already been taken.
    # Only meaningful for virtual cards.
    unwrapped = False

    def __init__(self, suit=NOTSET, number=0, resides_in=None, track_id=0):
        self.sync_id    = 0         # Synchronization id, changes during shuffling, kept sync between client and server.
        self.track_id   = track_id  # Card identifier, unique among all cards, 0 if doesn't care.
        self.suit       = suit
        self.number     = number
        self.resides_in = resides_in

    def __data__(self):
        return dict(
            type=self.__class__.__name__,
            suit=self.suit,
            number=self.number,
            sync_id=self.sync_id,
            track_id=self.track_id,
        )

    def sync(self, data):  # this only executes at client side, let it crash.
        if data['sync_id'] != self.sync_id:
            logging.error(
                'CardOOS: server: %s, %s, %s, sync_id=%d; client: %s, %s, %s, sync_id=%d',

                data['type'],
                self.SUIT_REV.get(data['suit'], data['suit']),
                self.NUM_REV.get(data['number'], data['number']),
                data['sync_id'],

                self.__class__.__name__,
                self.SUIT_REV.get(self.suit),
                self.NUM_REV.get(self.number),
                self.sync_id,
            )
            raise GameError('Card: out of sync')

        clsname = data['type']
        cls = Card.card_classes.get(clsname)

        if not cls:
            raise GameError('Card: unknown card class')

        self.__class__ = cls
        self.suit = data['suit']
        self.number = data['number']
        self.track_id = data['track_id']

    def conceal(self):
        self.__class__ = HiddenCard
        self.suit = self.number = self.track_id = 0

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
            num=self.NUM_REV.get(self.number, self.number),
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


class PhysicalCard(Card):
    def __eq__(self, other):
        if not isinstance(other, Card): return False
        return self.sync_id == other.sync_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 84065234 + self.sync_id


class VirtualCard(Card):
    sort_index = 0
    sync_id = 0
    usage = 'none'

    def __init__(self, player):
        self.player           = player
        self.associated_cards = []
        self.resides_in       = player.cards
        self.action_params    = {}
        self.unwrapped        = False
        self._suit            = None
        self._number          = None
        self._color           = None

    def __data__(self):
        return {
            'class':  self.__class__.__name__,
            'sync_id': self.sync_id,
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
        vc.associated_cards = cl[:]
        return vc

    def get_color(self):
        if self._color is not None:
            return self._color

        color = set([c.color for c in self.associated_cards])
        color = color.pop() if len(color) == 1 else Card.NOTSET
        return color

    def set_color(self, v):
        self._color = v

    color = property(get_color, set_color)

    def get_number(self):
        if self._number is not None:
            return self._number

        num = set([c.number for c in self.associated_cards])
        num = num.pop() if len(num) == 1 else Card.NOTSET
        return num

    def set_number(self, v):
        self._number = v

    number = property(get_number, set_number)

    def get_suit(self):
        if self._suit is not None:
            return self._suit

        cl = self.associated_cards
        suit = cl[0].suit if len(cl) == 1 else Card.NOTSET
        return suit

    def set_suit(self, v):
        self._suit = v

    suit = property(get_suit, set_suit)

    def sync(self, data):
        assert data['vcard']
        assert self.__class__.__name__ == data['class']
        assert self.sync_id == data['sync_id']
        assert self.action_params == data['params']

    @staticmethod
    def find_in_hierarchy(card, cls):
        if card.is_card(cls):
            return card

        if not card.is_card(VirtualCard):
            return None

        for c in card.associated_cards:
            r = VirtualCard.find_in_hierarchy(c, cls)
            if r: return r

        return None


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

    def __eq__(self, rhs):
        # two empty card lists is not the same.
        # card list never equals to a deque.
        return self is rhs

    def __repr__(self):
        return "CardList(owner=%s, type=%s, len == %d)" % (self.owner, self.type, len(self))


class Deck(GameObject):
    def __init__(self, card_definition=None):
        from thb.cards import definition
        card_definition = card_definition or definition.card_definition

        self.cards_record = {}
        self.vcards_record = WeakValueDictionary()
        self.droppedcards = CardList(None, 'droppedcard')
        self.collected_ppoints = CardList(None, 'collected_ppoints')
        cards = CardList(None, 'deckcard')
        self.cards = cards
        cards.extend(
            cls(suit, rank, cards, track_id=alloc_id())
            for cls, suit, rank in card_definition
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
            l = [c.__class__(c.suit, c.number, cl, c.track_id) for c in dropped[:-10]]
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
        assert not card.sync_id
        sid = Game.getgame().get_synctag()
        card.sync_id = sid
        self.cards_record[sid] = card
        return sid

    def register_vcard(self, vc):
        sid = Game.getgame().get_synctag()
        vc.sync_id = sid
        self.vcards_record[sid] = vc
        return sid

    def shuffle(self, cl):
        owner = cl.owner
        list_shuffle(cl, owner)

        for c in cl:
            c.sync_id = 0
            self.register_card(c)

    def inject(self, cls, suit, rank):
        cl = self.cards
        c = cls(suit, rank, cl)
        self.register_card(c)
        cl.appendleft(c)
        return c


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
        if cls is PhysicalCard:
            return False

        if issubclass(self.treat_as, cls):
            return True

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


class DummyCard(Card):  # another special thing....
    associated_action = None
    target = t_None
    category = ('dummy', )

    def __init__(self, suit=Card.NOTSET, number=0, resides_in=None, **kwargs):
        Card.__init__(self, suit, number, resides_in)
        self.__dict__.update(kwargs)
