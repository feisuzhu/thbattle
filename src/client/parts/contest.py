# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, Sequence

# -- third party --
# -- own --
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class Contest(object):
    def __init__(self, core: Core):
        self.core = core

    # ----- Public Methods -----
    def setup(self, name: str, mode: str, pids: Sequence[int]) -> None:
        core = self.core
        core.server.write(wire.msg.SetupContest(name=name, mode=mode, pids=list(pids)))
