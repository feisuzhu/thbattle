# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import Enum
from itertools import cycle
from typing import Any, Dict, Generic, Iterable, List, Optional, Sequence, TYPE_CHECKING, Tuple
from typing import Type, TypeVar, TypedDict
import logging
import random

# -- third party --
# -- own --
from game.base import GameViralContext, Player, get_seed_for, sync_primitive
from thb.item import GameItem
from thb.mode import THBattle
from utils.misc import BatchList, partition
import settings

# -- typing --
if TYPE_CHECKING:
    from thb.characters.base import Character  # noqa: F401


# -- code --
log = logging.getLogger('thb.common')


class CharChoice(GameViralContext):
    chosen: Any = None
    char_cls: Optional[Type[Character]]

    def __init__(self, char_cls=None) -> None:
        self.set(char_cls)

    def dump(self):
        assert self.char_cls
        return self.char_cls.__name__

    def sync(self, data) -> None:
        from thb.characters.base import Character
        self.set(Character.classes[data])

    def conceal(self) -> None:
        self.char_cls = None
        self.chosen = None

    def set(self, char_cls) -> None:
        self.char_cls = char_cls

    def __repr__(self):
        return '<Choice: {}>'.format(
            'None' if not self.char_cls else self.char_cls.__name__,
        )


T = TypeVar('T', bound=Enum)


class PlayerRole(Generic[T], GameViralContext):
    _role: T

    def __init__(self, typ: Type[T]):
        self._typ = typ
        self._role = typ(0)

    def __str__(self) -> str:
        return self._role.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self._typ):
            return False

        return self._role == other

    def dump(self) -> Any:
        return self._role.value

    def sync(self, data) -> None:
        self._role = self._typ(data)

    '''
    def is_type(self, t: Enum) -> bool:
        g = self.game
        pl = g.players
        return sync_primitive(self.identity == t, pl)
    '''

    def set(self, t: T) -> None:
        assert isinstance(t, self._typ)
        if self.game.is_server_side():
            self._role = self._typ(t)

    def get(self) -> T:
        return self._role


def roll(g: THBattle, pl: BatchList[Player], items: Dict[Player, List[GameItem]]) -> BatchList[Player]:
    from thb.item import European
    roll = list(range(len(pl)))
    g.random.shuffle(roll)
    eu = European.get_european(g, items)
    if eu:
        i = pl.index(eu)
        roll.remove(i)
        roll.insert(0, i)

    roll = sync_primitive(roll, pl)
    roll = BatchList(pl[i] for i in roll)
    g.emit_event('game_roll', roll)
    return roll


class BuildChoicesSpec(TypedDict):
    num: int


class VirtualPlayer(Player):

    def __init__(self, players: Sequence[Player]):
        self.players = players
        super().__init__()

    def reveal(self, obj: Any):
        for p in self.players:
            p.reveal(obj)


def build_choices_shared(g: THBattle,
                         players: BatchList[Player],
                         items: Dict[Player, List[GameItem]],
                         candidates: List[Type[Character]],
                         spec: BuildChoicesSpec,
                         ) -> Tuple[List[CharChoice], Dict[Player, CharChoice]]:
    p = VirtualPlayer(players)
    choices, imperial = build_choices(g, players, items, candidates, {p: spec})
    return choices[p], imperial


def build_choices(g: THBattle,
                  players: BatchList[Player],
                  items: Dict[Player, List[GameItem]],
                  candidates: List[Type[Character]],
                  spec: Dict[Player, BuildChoicesSpec],
                  ) -> Tuple[Dict[Player, List[CharChoice]], Dict[Player, CharChoice]]:

    from thb.item import ImperialChoice

    # ----- testing -----
    from thb.characters.base import Character

    testing_lst: Iterable[str] = settings.TESTING_CHARACTERS
    testing = list(Character.classes[i] for i in testing_lst)
    candidates, _ = partition(lambda c: c not in testing, candidates)

    if g.is_server_side():
        candidates = list(candidates)
        g.random.shuffle(candidates)
    else:
        candidates = [None] * len(candidates)

    assert sum(s['num'] for p, s in spec.items()) <= len(candidates) + len(testing), 'Insufficient choices'

    result: Dict[Player, List[CharChoice]] = {p: [] for p in spec}

    players_for_testing = list(spec)

    candidates = list(candidates)
    seed = get_seed_for(g, players)
    shuffler = random.Random(seed)
    shuffler.shuffle(players_for_testing)

    for e, cls in zip(cycle(players_for_testing), testing):
        result[e].append(CharChoice(cls))

    # ----- imperial (force chosen by ImperialChoice) -----
    imperial = ImperialChoice.get_chosen(items, players)
    imperial = {p: CharChoice(cls) for p, cls in imperial.items()}

    for p, c in imperial.items():
        result[p].append(c)

    # ----- normal -----
    for p, s in spec.items():
        for _ in range(len(result[p]), s['num']):
            result[p].append(CharChoice(candidates.pop()))

    # ----- compose final result, reveal, and return -----
    for p, l in result.items():
        p.reveal(l)

    return result, imperial
