# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, TYPE_CHECKING, TypedDict

# -- third party --
# -- own --
from client.base import ClientGameRunner
from thb.cards.base import Card
from thb.meta.tags import TagAnimation, get_display_tags

# -- typing --
if TYPE_CHECKING:
    from thb.characters.base import Character  # noqa: F401
    from thb.meta.actions import CardView  # noqa: F401
    from thb.mode import THBattle  # noqa: F401


# -- code --
class GameState(TypedDict):
    characters: List[CharacterState]
    me: TheoneState


class CharacterState(TypedDict):
    pid: int
    character: str
    life: int
    maxlife: int
    vitality: int
    role: str
    cards: List[CardListView]
    tags: List[TagAnimation]


class TheoneState(TypedDict):
    pid: int


class CardListView(TypedDict):
    type: str
    cards: List[CardView]


def state_of(g: THBattle) -> GameState:
    runner = g.runner
    assert isinstance(runner, ClientGameRunner)
    core = runner.core
    chs: List[CharacterState] = []
    me = core.game.theone_of(g)

    for ch in g.players:
        chs.append({
            'pid': ch.player.pid,
            'character': ch.__class__.__name__,
            'life': ch.life,
            'maxlife': ch.maxlife,
            'vitality': ch.tags['vitality'],
            'role': 'what?',
            'cards': [{
                'type': cl.type,
                'cards': [Card.dump(c) for c in cl],
            } for cl in ch.lists],
            'tags': get_display_tags(g, ch),
        })

    return {
        'characters': chs,
        'me': {
            'pid': me.pid,
        },
    }


{
    'characters': [{
        'pid': 2,
        'character': 'Youmu',
        'life': 3,
        'maxlife': 4,
        'vitality': 1,
        'role': 'HIDDEN',
        'cards': [{
            'name': 'cards',
            'cards': [{
                'type': 'card',
                'card': 'HiddenCard',
                'shown': False,
                'suit': 0,
                'number': 0,
                'sync_id': 1234,
            }, ...],
        }, {
            'name': 'equips',
            'cards': [{
                'type': 'card',
                'card': 'LaevateinCard',
                'shown': True,
                'suit': 1,
                'number': 1,
                'sync_id': 1234,
            }, ...],
        }, ...],
        'tags': [{
            'sprite': 'thb-whatever-tag',
            'desc': 'Holy Fucking Shit!!!'
        }, ...],
    }, ...],
    'me': {
        'pid': 2,
    },
}
