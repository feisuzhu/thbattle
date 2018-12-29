# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List

# -- third party --
from mypy_extensions import TypedDict

# -- own --


# -- code --
class User(TypedDict):
    uid: int
    state: str


class Game(TypedDict):
    gid: int
    type: str
    name: str
    started: bool
    online: int


class GameDetail(Game):
    users: List[User]
    params: Dict[str, Any]
    items: Dict[int, List[str]]
