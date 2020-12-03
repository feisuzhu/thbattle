# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, List, TYPE_CHECKING, TypedDict


# -- third party --
# -- own --
import wire


# -- typing --
if TYPE_CHECKING:
    from client.base import Game  # noqa: F401
    from client.core import Core  # noqa: F401


# -- code --
class View(object):
    def __init__(self, core: Core):
        self.core = core

    def __repr__(self) -> str:
        return self.__class__.__name__
