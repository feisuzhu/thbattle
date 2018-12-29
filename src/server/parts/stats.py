# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING
import logging

# -- third party --
# -- own --
# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.stats')


class Stats(object):
    def __init__(self, core: Core):
        self.core = core

    def __repr__(self) -> str:
        return self.__class__.__name__
