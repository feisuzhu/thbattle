# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import deque
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Sequence, TYPE_CHECKING, Tuple
from typing import Type
from weakref import WeakValueDictionary
import itertools
import logging
import random
from typing import TypedDict

# -- third party --

# -- own --
from game.base import GameError, GameObject, GameViralContext, get_seed_for, Nobody
from thb.mode import THBattle

# -- typing --
if TYPE_CHECKING:
    from thb.actions import UserAction  # noqa: F401
    from thb.characters.base import Character  # noqa: F401
    from thb.meta.typing import CardMeta, SkillMeta  # noqa: F401


# -- code --
log = logging.getLogger('THBattle_Cards')
alloc_id = itertools.count(1).__next__


class CardView(TypedDict, total=False):
    type: str
    vcard: bool
    suit: int
    number: int
    color: str
    sync_id: int
    track_id: int
    params: Optional[Dict[str, Any]]


class Card(GameObject, GameViralContext):
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

    _color: Optional[int] = None
    usage = 'launch'

    ui_meta: ClassVar[CardMeta]

    associated_action: Optional[Type[UserAction]]
    category: Sequence[str]

    # True means this card's associated cards have already been taken.
    # Only meaningful for virtual cards.
    unwrapped = False

    def __init__(self, suit=NOTSET, number=0, resides_in=None, track_id=0):
        self.sync_id    = 0         # Synchronization id, changes during shuffling, kept sync between client and server.
        self.track_id   = track_id  # Card identifier, unique among all cards, 0 if doesn't care, or not known.
        self.suit       = suit
        self.number     = number
        self.resides_in = resides_in

    def dump(self, with_meta=False, with_description=False) -> CardView:
        return {
            'type': self.__class__.__name__,
            'vcard': False,
            'suit': self.suit,
            'number': self.number,
            'color': self.color,
            'sync_id': self.sync_id,
            'track_id': self.track_id,
            'params': None,
        }

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
        cls = PhysicalCard.classes.get(clsname)

        if not cls:
            raise GameError('Card: unknown card class')

        self.__class__ = cls
        self.suit = data['suit']
        self.number = data['number']
        self.track_id = data['track_id']

    @staticmethod
    def copy(o):
        return o.__class__(
            o.suit,
            o.number,
            o.resides_in,
            o.track_id,
        )

    def shred(self):
        self.__class__ = ShreddedCard
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
        return "{name}({suit}.{num}{detached}, {sync_id})".format(
            name=self.__class__.__name__,
            suit=self.SUIT_REV.get(self.suit, self.suit),
            num=self.NUM_REV.get(self.number, self.number),
            detached='*' if self.detached else '',
            sync_id=self.sync_id,
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

    def target(self: Any, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        raise Exception('Override this')


class PhysicalCard(Card):
    classes: ClassVar[Dict[str, Type[PhysicalCard]]] = {}

    def __eq__(self, other):
        if not isinstance(other, Card): return False
        return self.sync_id == other.sync_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 84065234 + self.sync_id


class VirtualCard(Card, GameViralContext):
    associated_cards: Sequence[Card]
    action_params: dict
    no_reveal: ClassVar[bool] = False
    game: THBattle

    _suit: Optional[int]
    _number: Optional[int]
    _color: Optional[int]

    def __init__(self, character: Character):
        self.character        = character
        self.associated_cards = []
        self.resides_in       = character.cards
        self.action_params    = {}
        self.unwrapped        = False
        self.sync_id          = 0
        self.track_id         = 0
        self.usage            = 'none'
        self._suit            = None
        self._number          = None
        self._color           = None

    def dump(self):
        return {
            'type':  self.__class__.__name__,
            'vcard': True,
            'suit': self.suit,
            'number': self.number,
            'color': self.color,
            'sync_id': self.sync_id,
            'track_id': -1,
            'params': self.action_params,
        }

    def check(self):  # override this
        return False

    @classmethod
    def unwrap(cls, vcards: Iterable[Card], include_vcards: bool = False) -> List[Card]:
        lst: List[Card] = []
        sl = list(vcards)

        while sl:
            s = sl.pop()
            if isinstance(s, VirtualCard):
                if include_vcards:
                    lst.append(s)
                sl.extend(VirtualCard.unwrap(s.associated_cards, include_vcards))
            else:
                assert isinstance(s, (PhysicalCard, HiddenCard)), s
                lst.append(s)

        return lst

    @classmethod
    def wrap(cls, cl: Sequence[Card], character: Character, params: Dict[str, Any] = None):
        vc = cls(character)
        vc.action_params = params or {}
        vc.associated_cards = cl[:]
        return vc

    def get_color(self):
        if self._color is not None:
            return self._color

        color = {c.color for c in self.associated_cards}
        color = color.pop() if len(color) == 1 else Card.NOTSET
        return color

    def set_color(self, v):
        self._color = v

    color = property(get_color, set_color)

    def get_number(self):
        if self._number is not None:
            return self._number

        num = {c.number for c in self.associated_cards}
        num = num.pop() if len(num) == 1 else Card.NOTSET
        return num

    def set_number(self, v):
        self._number = v

    number = property(get_number, set_number)

    def get_suit(self) -> int:
        if self._suit is not None:
            return self._suit

        cl = self.associated_cards
        suit = cl[0].suit if len(cl) == 1 else Card.NOTSET
        return suit

    def set_suit(self, v: int):
        self._suit = v

    suit = property(get_suit, set_suit)

    def sync(self, data):
        assert data['vcard']
        assert self.__class__.__name__ == data['type']
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

    def __init__(self, owner: Optional['Character'], typ: str):
        self.owner = owner
        self.type = typ
        deque.__init__(self)

    def __eq__(self, rhs):
        # two empty card lists is not the same.
        # card list never equals to a deque.
        return self is rhs

    def __repr__(self):
        return "CardList(owner=%s, type=%s, len == %d)" % (self.owner, self.type, len(self))


class Deck(GameObject):
    def __init__(self, g: THBattle, card_definition=None):
        from thb.cards import definition
        self.game = g
        card_definition = card_definition or definition.card_definition

        self.cards_record: Dict[int, PhysicalCard] = {}
        self.vcards_record: WeakValueDictionary[int, VirtualCard] = WeakValueDictionary()
        self.droppedcards = CardList(None, 'droppedcard')
        cards = CardList(None, 'deckcard')
        self.cards = cards
        cards.extend(
            cls(suit, rank, cards, track_id=alloc_id())
            for cls, suit, rank in card_definition
        )
        self.shuffle(cards)

    def getcards(self, num: int) -> List[Card]:
        cl = self.cards
        if len(self.cards) <= num:
            dcl = self.droppedcards

            assert all(not c.is_card(VirtualCard) for c in dcl)
            assert all(not c.is_card(ShreddedCard) for c in dcl)

            dropped = list(dcl)
            dcl.clear()
            rest = list(cl)
            cl.clear()

            dcl.extend(dropped[-10:])
            cl.extend([Card.copy(c) for c in dropped[:-10]])
            self.shuffle(cl)
            cl.extendleft(reversed(rest))

            # assert all(not isinstance(c, ShreddedCard) for c in cl)
            # assert rest == list(cl)[:len(rest)]

        cl = self.cards
        rst = []
        for i in range(min(len(cl), num)):
            rst.append(cl[i])

        return rst

    def lookup(self, sync_id: int) -> Optional[Card]:
        return self.vcards_record.get(sync_id, None) or \
            self.cards_record.get(sync_id, None)

    def register_card(self, card: PhysicalCard):
        assert not card.sync_id
        g = self.game
        sid = g.get_synctag()
        card.sync_id = sid
        self.cards_record[sid] = card
        return sid

    def register_vcard(self, vc: VirtualCard):
        g = self.game
        sid = g.get_synctag()
        vc.sync_id = sid
        self.vcards_record[sid] = vc
        return sid

    def shuffle(self, cl: CardList):
        owner = cl.owner.player if cl.owner else Nobody()

        g = self.game

        # assert all(c.resides_in is cl for c in cl)

        seed = get_seed_for(g, owner)

        if seed:  # cardlist owner & server
            cards = [Card.copy(c) for c in cl]
            shuffler = random.Random(seed)
            shuffler.shuffle(cards)
        else:  # others
            cards = [HiddenCard() for c in cl]

        for c in cl:
            c.shred()

        for c in cards:
            c.resides_in = cl

        cl.clear()
        cl.extend(cards)

        for c in cl:
            self.register_card(c)

        # assert all(not isinstance(c, ShreddedCard) for c in cl)

    def inject(self, cls: Type[PhysicalCard], suit: int, rank: int) -> PhysicalCard:
        cl = self.cards
        c = cls(suit, rank, cl)
        self.register_card(c)
        cl.appendleft(c)
        return c


class Skill(VirtualCard):
    category: Sequence[str] = ['skill']
    skill_category: Sequence[str] = []

    ui_meta: ClassVar[SkillMeta]

    def __init__(self, character):
        assert character is not None
        VirtualCard.__init__(self, character)
        self.usage = 'launch'

    def check(self):  # override this
        return False


class TreatAs(object):
    treat_as: Type[PhysicalCard]
    usage = 'launch'

    if TYPE_CHECKING:
        category: Sequence[str] = ['skill', 'treat_as']
    else:
        @property
        def category(self) -> Sequence[str]:
            return ['skill', 'treat_as'] + list(self.treat_as.category)

    def check(self):
        return False

    def is_card(self, cls):
        if cls is PhysicalCard:
            return False

        if issubclass(self.treat_as, cls):
            return True

        return isinstance(self, cls)

    def target(self: Any, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        return self.treat_as().target(src, tl)

    def __getattr__(self, name):
        return getattr(self.treat_as, name)


# card targets:
def t_None():
    def t_None(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        return ([], False)
    return t_None


def t_Self():
    def t_Self(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        return ([src], True)
    return t_Self


def t_OtherOne():
    def t_OtherOne(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(src)
        except ValueError:
            pass
        return (tl[-1:], bool(len(tl)))
    return t_OtherOne


def t_One():
    def t_One(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        tl = [t for t in tl if not t.dead]
        return (tl[-1:], bool(len(tl)))
    return t_One


def t_All():
    def t_All(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        g = self.game
        return ([t for t in g.players.rotate_to(src)[1:] if not t.dead], True)
    return t_All


def t_AllInclusive():
    def t_AllInclusive(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        g = self.game
        pl = g.players.rotate_to(src)
        return ([t for t in pl if not t.dead], True)
    return t_AllInclusive


def t_OtherLessEqThanN(n):
    def t_OtherLessEqThanN(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(src)
        except ValueError:
            pass
        return (tl[:n], bool(len(tl)))

    t_OtherLessEqThanN._for_test_OtherLessEqThanN = n  # type: ignore
    return t_OtherLessEqThanN


def t_OneOrNone():
    def t_OneOrNone(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        tl = [t for t in tl if not t.dead]
        return (tl[-1:], True)
    return t_OneOrNone


def t_OtherN(n):
    def t_OtherN(self, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(src)
        except ValueError:
            pass
        return (tl[:n], bool(len(tl) >= n))

    t_OtherN._for_test_OtherN = n  # type: ignore
    return t_OtherN


class HiddenCard(Card):  # special thing....
    associated_action = None
    target = t_None()


class ShreddedCard(Card):  # Become this after shuffling
    associated_action = None
    target = t_None()


class DummyCard(PhysicalCard):  # another special thing....
    associated_action = None
    target = t_None()
    category = ['dummy']

    def __init__(self, suit=Card.NOTSET, number=0, resides_in=None, **kwargs):
        Card.__init__(self, suit, number, resides_in)
        self.__dict__.update(kwargs)
