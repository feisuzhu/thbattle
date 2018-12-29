# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import Enum
from typing import Dict, List, Optional, Sequence, TYPE_CHECKING, Tuple

# -- third party --
from mypy_extensions import TypedDict
from typing_extensions import Protocol

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
    roles_disp: Dict[Enum, str]


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

    def is_action_valid(self, g: THBattle, cl: Sequence[Card], tl: Sequence[Character]) -> Tuple[bool, str]:
        ...

    def sound_effect(self, act: THBAction) -> Optional[str]:
        ...


class SkillMeta(CardMeta):
    def clickable(self, g: THBattle) -> bool:
        ...

    def is_complete(self, g: THBattle, c: Skill) -> Tuple[bool, str]:
        ...
