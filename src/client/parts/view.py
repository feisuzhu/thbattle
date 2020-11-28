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
class CardMetaView(TypedDict):
    name: str
    image: str
    desc: Optional[str]
    eqpcat: str
    skcat: List[str]
    nodisp: bool
    ui: str


class View(object):
    def __init__(self, core: Core):
        self.core = core

    def __repr__(self) -> str:
        return self.__class__.__name__

    def Character(self, ch: Character):
        pass

    def Card(self, c: Card, with_description=False) -> CardView:
        rst: CardView = {
            'type': self.__class__.__name__,
            'vcard': False,
            'suit': self.suit,
            'number': self.number,
            'color': self.color,
            'sync_id': self.sync_id,
            'track_id': self.track_id,
            'params': {},
            'm': None,
        }

        rst = c.dump()

        if with_meta:
            m = self.ui_meta
            meta: CardMetaView = {
                'name': self.ui_meta.name,
                'image': self.ui_meta.image,
                'eqpcat': getattr(self, 'equipment_category', None),
                'skcat': getattr(self, 'skill_category', None),
                'nodisp': getattr(m, 'no_display', False),
                'ui': getattr(m, 'params_ui', None),
                'desc': None,
            }
            if with_description:
                meta['desc'] = getattr(m, 'description', None)

            rst['m'] = meta

        return rst
