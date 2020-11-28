# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, List, Optional, TYPE_CHECKING, TypedDict, cast

# -- third party --
# -- own --
from client.base import ClientGameRunner
from thb.meta import view
from thb.meta.tags import TagAnimation, get_display_tags
from thb.mode import THBattle

# -- typing --
if TYPE_CHECKING:
    from thb.actions import UserAction  # noqa: F401
    from thb.characters.base import Character  # noqa: F401
    from thb.meta.actions import CardView  # noqa: F401
    from thb.meta.typing import CardMeta, SkillMeta  # noqa: F401


# -- code --
class CardMetaView(TypedDict, total=False):
    type: str
    suit: int
    number: int
    color: str
    sync_id: int
    track_id: int
    params: Optional[Dict[str, Any]]
    name: str
    image: str
    desc: Optional[str]
    eqpcat: str


class CardListView(TypedDict):
    type: str
    cards: List[CardMetaView]


def card(c, with_description=False) -> CardMetaView:
    m = c.ui_meta
    rst: CardMetaView = {
        'type': c.__class__.__name__,
        'suit': c.suit,
        'number': c.number,
        'color': c.color,
        'sync_id': c.sync_id,
        'track_id': c.track_id,
        'params': getattr(c, 'action_params', None),

        'name': c.ui_meta.name,
        'image': c.ui_meta.image,
        'eqpcat': getattr(c, 'equipment_category', None),
    }

    if with_description:
        rst['desc'] = getattr(m, 'description', None)

    rst = {k: v for k, v in rst.items() if v is not None}
    return cast(CardMetaView, rst)


class CharacterView(TypedDict):
    pid: int
    type: str
    life: int
    maxlife: int
    dead: bool
    cards: List[CardListView]
    tags: List[TagAnimation]

    name: str
    portrait: str
    figure: str


def character(ch, with_description=False) -> CharacterView:
    m = ch.ui_meta
    return {
        'pid': ch.player.pid,
        'type': ch.__class__.__name__,
        'life': ch.life,
        'maxlife': ch.maxlife,
        'dead': ch.dead,
        'cards': [{
            'type': cl.type,
            'cards': [card(c) for c in cl],
        } for cl in ch.lists],
        'tags': get_display_tags(ch),

        'name': m.name,
        'portrait': m.port_image,
        'figure': m.figure_image,
    }


class SkillView(TypedDict, total=False):
    type: str
    name: str
    desc: str
    skcat: List[str]
    ui: str
    clickable: bool


def skill(sk) -> SkillView:
    m = sk.ui_meta
    return {
        'type': sk.__name__,
        'name': m.name,
        'desc':  m.description,
        'skcat': sk.skill_category,
        'ui': getattr(sk, 'params_ui', None),
        'clickable': sk.ui_meta.clickable(),
    }


class GameState(TypedDict):
    characters: List[view.CharacterView]
    deck_remaining: int
    my_pid: int
    my_skills: List[view.SkillView]


def state_of(g: THBattle) -> GameState:
    runner = g.runner
    assert isinstance(runner, ClientGameRunner)
    core = runner.core
    chs: List[view.CharacterView] = []
    me = core.game.theone_of(g)

    for ch in g.players:
        if ch.player is me:
            p = ch
        chs.append(character(ch))

    return {
        'characters': chs,
        'deck_remaining': len(g.deck.cards),
        'my_pid': me.pid,
        'my_skills': [
            skill(sk) for sk in p.skills
            if not getattr(sk, 'no_display', False)
        ],
    }
