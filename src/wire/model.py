# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List, TypedDict

# -- third party --
# -- own --


# -- code --
class User(TypedDict):
    pid: int
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
