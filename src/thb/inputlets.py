# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, Iterable, List, TYPE_CHECKING, Type, Union
import logging

# -- third party --
# -- own --
# -- typing --
if TYPE_CHECKING:
    from thb.actions import CardChooser, CharacterChooser  # noqa: F401
    from thb.characters.base import Character  # noqa: F401

# -- errord --
from game.base import Inputlet, Player
from thb.cards.base import Card, Skill
from thb.common import CharChoice
from utils.check import CheckFailed, check, check_type


# -- code --
log = logging.getLogger('Inputlets')


class ChooseOptionInputlet(Inputlet):
    def __init__(self, initiator: Any, options: Iterable):
        self.initiator = initiator
        self.options = options
        self.result = None

    def parse(self, data):
        if data not in self.options:
            return None

        return data

    def data(self):
        return self.result

    def set_option(self, value):
        'For UI'
        self.result = value


class ActionInputlet(Inputlet):
    initiator: Union[CardChooser, CharacterChooser]
    actor: Character

    def __init__(self, initiator: Union[CardChooser, CharacterChooser], categories: Iterable[str], candidates: Iterable[object]):
        self.initiator = initiator

        self.categories = categories
        self.candidates = candidates

        self.skills: List[Type[Skill]] = []
        self.cards: List[Card] = []
        self.players: List[Player] = []
        self.params: Dict[str, Any] = {}

    def parse(self, data):
        # data = [
        #     [skill_index1, ...],
        #     [card_sync_id1, ...],
        #     [player_id1, ...],
        #     {'action_param1': 'AttackCard'},
        # ]

        actor = self.actor
        g = self.game
        categories = self.categories
        categories = [getattr(actor, i) for i in categories] if categories else None
        candidates = self.candidates

        skills: List[Type[Skill]] = []
        cards: List[Card] = []
        players: List[Player] = []
        params: Dict[str, Any] = {}

        try:
            check_type([[int, ...]] * 3 + [dict], data)  # type: ignore

            sid_list, cid_list, pid_list, params = data

            if candidates:
                check(candidates)
                pl = [g.player_fromid(i) for i in pid_list]
                check(all([p in candidates for p in pl]))
                players = pl

            if categories:
                cards = [g.deck.lookup(i) for i in cid_list]
                check(len(cards) == len(cid_list))  # Invalid id

                cs = set(cards)
                check(len(cs) == len(cid_list))  # repeated ids

                if sid_list:
                    assert actor.cards in categories or actor.showncards in categories
                    check(all(cat.owner is actor for cat in categories))
                    check(all(c.resides_in.owner is actor for c in cards))  # Cards belong to actor?
                    for skill_id in sid_list:
                        check(0 <= skill_id < len(actor.skills))
                    skills = [actor.skills[i] for i in sid_list]
                else:
                    check(all(c.resides_in in categories for c in cards))  # Cards in desired categories?

            return (skills, cards, players, params)

        except CheckFailed:
            return None

    def data(self):
        g = self.game
        actor_skills = self.actor.skills
        sid_list = [actor_skills.index(s) for s in self.skills]
        cid_list = [c.sync_id for c in self.cards]
        pid_list = [g.get_playerid(p) for p in self.players]
        return [sid_list, cid_list, pid_list, self.params]

    def set_result(self, skills, cards, players, params=None):
        self.skills = skills
        self.cards = cards
        self.players = players
        self.params = params or {}


class ChooseIndividualCardInputlet(Inputlet):
    def __init__(self, initiator: Any, cards: List[Card]):
        self.initiator = initiator
        self.cards = cards
        self.selected = None

    def parse(self, data):
        try:
            cid = data
            check(isinstance(cid, int))
            cards = [c for c in self.cards if c.sync_id == cid]
            check(len(cards))  # Invalid id
            return cards[0]

        except CheckFailed:
            return None

    def data(self):
        sel = self.selected
        return sel.sync_id if sel else None

    def set_card(self, c):
        assert c in self.cards
        self.selected = c

    def post_process(self, actor, card):
        if card:
            log.debug('ChooseIndividualCardInputlet: detaching %r!', card)
            card.detach()

        return card


class ChoosePeerCardInputlet(Inputlet):
    def __init__(self, initiator: Any, target: Character, categories: Iterable[str]):
        self.initiator = initiator
        self.target = target
        self.categories = categories
        self.selected = None

    def parse(self, data):
        target = self.target
        categories = self.categories
        categories = [getattr(target, i) for i in categories]

        assert all(c.owner is target for c in categories)
        try:
            check(sum(len(c) for c in categories))  # no cards at all

            cid = data
            g = self.game

            check(isinstance(cid, int))

            card = g.deck.lookup(cid)
            check(card)  # Invalid id

            check(card.resides_in.owner is target)
            check(card.resides_in in categories)

            return card

        except CheckFailed:
            return None

    def data(self):
        sel = self.selected
        return sel.sync_id if sel else None

    def set_card(self, c):
        assert c.resides_in.type in self.categories
        self.selected = c

    def post_process(self, actor, card):
        if card:
            log.debug('ChoosePeerCardInputlet: detaching %r!', card)
            card.detach()

        return card


class ProphetInputlet(Inputlet):
    '''For Ran'''
    def __init__(self, initiator: Any, cards: List[Card]):
        self.initiator = initiator
        self.cards = cards
        self.upcards: List[Card] = []
        self.downcards: List[Card] = []

    def parse(self, data):
        try:
            check_type([[int, ...]] * 2, data)
            upcards = data[0]
            downcards = data[1]
            check(sorted(upcards + downcards) == list(range(len(self.cards))))
        except CheckFailed:
            return [self.cards, []]

        cards = self.cards
        upcards = [cards[i] for i in upcards]
        downcards = [cards[i] for i in downcards]

        return [upcards, downcards]

    def data(self):
        cards = self.cards
        upcards = self.upcards
        downcards = self.downcards
        if not set(cards) == set(upcards + downcards):
            return [list(range(len(self.cards))), []]

        upcards = [cards.index(c) for c in upcards]
        downcards = [cards.index(c) for c in downcards]
        return [upcards, downcards]

    def set_result(self, upcards, downcards):
        assert set(self.cards) == set(upcards + downcards)
        self.upcards = upcards
        self.downcards = downcards


class ChooseGirlInputlet(Inputlet):
    def __init__(self, initiator: Any, mapping: Dict[Player, List[CharChoice]]):
        self.initiator = initiator

        m = dict(mapping)
        for k in m:
            assert all([isinstance(i, CharChoice) for i in m[k]])
            m[k] = m[k][:]

        self.mapping = m
        self.choice = None

    def parse(self, i):
        m = self.mapping
        actor = self.actor
        try:
            check(actor in m)
            check_type(int, i)
            check(0 <= i < len(m[actor]))
            choice = m[actor][i]
            check(not choice.chosen)
            return choice
        except CheckFailed:
            return None

    def data(self):
        if self.choice is None:
            return None

        try:
            return self.mapping[self.actor].index(self.choice)
        except Exception:
            log.exception('WTF?!')
            return None

    def set_choice(self, choice):
        assert choice in self.mapping[self.actor]
        self.choice = choice


class SortCharacterInputlet(Inputlet):
    def __init__(self, initiator: Any, mapping: Dict[Player, List[CharChoice]], limit: int=10000):
        self.initiator = initiator

        s = {len(l) for l in list(mapping.values())}
        assert(len(s) == 1)
        self.num = n = s.pop()
        self.limit = limit if n >= limit else n
        self.mapping = mapping
        self.result = list(range(n))

    def parse(self, data):
        n = self.num
        try:
            check(data)
            check_type([int] * n, data)
            check(set(data) == set(range(n)))
            return data

        except CheckFailed:
            return list(range(n))

    def data(self):
        assert set(self.result) == set(range(self.num))
        return self.result

    def set_result(self, result):
        assert set(result) == set(range(self.num))
        self.result = result


class HopeMaskInputlet(Inputlet):
    '''For Kokoro'''
    def __init__(self, initiator: Any, cards: List[Card]):
        self.initiator = initiator
        self.cards = cards
        self.putback: List[Card] = []
        self.acquire: List[Card] = []

    def parse(self, data):
        try:
            check_type([[int, ...]] * 2, data)
            putback = data[0]
            acquire = data[1]
            check(sorted(putback+acquire) == list(range(len(self.cards))))

            cards = self.cards
            putback = [cards[i] for i in putback]
            acquire = [cards[i] for i in acquire]

        except CheckFailed:
            return [self.cards, []]

        return [putback, acquire]

    def is_valid(self, putback, acquire):
        if not set(self.cards) == set(putback + acquire):
            return False

        if acquire:
            suit = acquire[0].suit
            if not all([c.suit == suit for c in acquire]):
                return False

        return True

    def data(self):
        cards = self.cards
        putback = self.putback
        acquire = self.acquire
        if not set(cards) == set(putback + acquire):
            return [list(range(len(self.cards))), []]

        putback = [cards.index(c) for c in putback]
        acquire = [cards.index(c) for c in acquire]
        return [putback, acquire]

    def set_result(self, putback, acquire):
        assert self.is_valid(putback, acquire)
        self.putback = putback
        self.acquire = acquire

    def post_process(self, actor, rst):
        g = self.game
        putback, acquire = rst
        g.players.exclude(actor).reveal(acquire)

        try:
            check(self.is_valid(putback, acquire))
        except CheckFailed:
            return [self.cards, []]

        return rst


class HopeMaskKOFInputlet(HopeMaskInputlet):

    @classmethod
    def tag(cls):
        return 'HopeMask'

    def is_valid(self, putback, acquire):
        if not set(self.cards) == set(putback + acquire):
            return False

        if len(acquire) > 1:
            return False

        return True


class GalgameDialogInputlet(Inputlet):
    def __init__(self, initiator: Any, character: Character, dialog: str, voice: str):
        self.initiator = initiator
        self.character = character
        self.dialog = dialog
        self.result = None
        self.voice = voice

    def parse(self, data):
        return data

    def data(self):
        return self.result

    def set_result(self, value):
        'For UI'
        self.result = value
