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
class Matching(object):
    def __init__(self, core: Core):
        self.core = core

    # ----- Public Methods -----
    def start(self, modes: Sequence[str]) -> None:
        core = self.core
        core.server.write(wire.msg.StartMatching(modes=list(modes)))

    def stop(self) -> None:
        core = self.core
        core.server.write(wire.msg.StartMatching(modes=[]))
