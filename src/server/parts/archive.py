# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, TYPE_CHECKING
import base64
import json
import logging
import time
import zlib

# -- third party --
import arrow

# -- own --
from server.base import Game, HumanPlayer
import settings

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Archive')


class Archive(object):
    def __init__(self, core: Core):
        self.core = core
        core.events.game_ended += self.handle_game_ended

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_game_ended(self, g: Game) -> Game:
        core = self.core

        meta = self._meta(g)
        archive = self._archive(g)

        core.backend.query('''
            mutation ArchiveGame($game: GameInput!, $archive: String!) {
              game {
                archive(game: $meta, archive: $archive) {
                  gid
                }
              }
            }
        ''', game=meta, archive=archive)

        return g

    # ----- Methods -----

    def _meta(self, g: Game) -> Dict[str, Any]:
        core = self.core
        start = core.room.start_time_of(g)
        flags = core.room.flags_of(g)

        if core.game.is_crashed(g):
            flags['crashed'] = True

        if core.game.is_aborted(g):
            flags['aborted'] = True

        return {
            'gid': core.room.gid_of(g),
            'name': core.room.name_of(g),
            'type': g.__class__.__name__,
            'flags': flags,
            'players': [core.auth.uid_of(u) for u in core.room.users_of(g)],
            'winners': [core.auth.uid_of(p.client) if isinstance(p, HumanPlayer) else 0 for p in core.game.winners_of(g)],
            'startedAt': arrow.get(start).to('Asia/Shanghai').isoformat(),
            'duration': int(time.time() - start),
        }

    def _archive(self, g: Game) -> str:
        core = self.core
        data = {
            'version': settings.VERSION,
            'gid': core.room.gid_of(g),
            'class': g.__class__.__name__,
            'params': core.game.params_of(g),
            'items': core.item.item_skus_of(g),
            'rngseed': core.game.rngseed_of(g),
            'players': [core.auth.uid_of(u) for u in core.room.users_of(g)],
            'data': core.game.get_gamedata_archive(g),
        }

        return base64.b64encode(
            zlib.compress(json.dumps(data).encode('utf-8'))
        ).decode('utf-8')
