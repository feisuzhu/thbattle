# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import Enum
from typing import Dict, List, Optional, Protocol, Sequence, TYPE_CHECKING, Tuple, TypedDict

# -- third party --
# -- own --
# -- typing --
if TYPE_CHECKING:
    from thb.cards.base import Card, Skill  # noqa: F401
    from thb.characters.base import Character  # noqa: F401
    from thb.mode import THBAction, THBattle  # noqa: F401


# -- code --
class ParamDisplayItem(TypedDict):
    desc: str
    options: List[Tuple[str, object]]


class ModeMeta(Protocol):
    name: str
    logo: str
    description: str
    params_disp: Dict[str, ParamDisplayItem]
    roles: Dict[Enum, str]


class CharacterMeta(Protocol):
    name: str
    title: str
    designer: str
    illustrator: str
    cv: str
    port_image: str
    figure_image: str
    miss_sound_effect: str


class CardMeta(Protocol):
    name: str
    image: str
    description: str

    def is_action_valid(self, c: Card, tl: Sequence[Character]) -> Tuple[bool, str]:
        ...

    def sound_effect(self, act: THBAction) -> Optional[str]:
        ...


class SkillMeta(CardMeta):
    def clickable(self) -> bool:
        ...

    def is_complete(self, c: Skill) -> Tuple[bool, str]:
        ...

    def is_available(self, ch: Character) -> bool:
        ...
