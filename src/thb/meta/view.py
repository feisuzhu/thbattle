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
    resides_in: Optional[str]
    owner: int
    name: str
    image: str
    desc: Optional[str]
    eqpcat: str


class CardListView(TypedDict):
    type: str
    name: str
    cards: List[CardMetaView]


def card(c, with_description=False) -> CardMetaView:
    m = c.ui_meta
    if (l := c.resides_in) is not None:
        resides_in = l.type
        owner = l.owner.get_player().pid if l.owner else 0
    else:
        resides_in = None
        owner = 0

    rst: CardMetaView = {
        'type': c.__class__.__name__,
        'suit': c.suit,
        'number': c.number,
        'color': c.color,
        'sync_id': c.sync_id,
        'track_id': c.track_id,
        'params': getattr(c, 'action_params', None),
        'resides_in': resides_in,
        'owner': owner,
        'name': c.ui_meta.name,
        'image': c.ui_meta.image,
        'eqpcat': getattr(c, 'equipment_category', None),
    }

    if with_description:
        rst['desc'] = getattr(m, 'description', None)

    rst = {k: v for k, v in rst.items() if v is not None}
    return cast(CardMetaView, rst)


class CharacterTypeView(TypedDict):
    type: str
    life: int
    maxlife: int
    name: str
    portrait: str
    figure: str
    desc: str


class CharacterView(CharacterTypeView):
    pid: int
    dead: bool
    cards: Optional[List[CardListView]]
    tags: Optional[List[TagAnimation]]


def character(ch, extra=True) -> CharacterView:
    m = ch.ui_meta
    return {
        'pid': ch.player.pid,
        'type': ch.__class__.__name__,
        'life': ch.life,
        'maxlife': ch.maxlife,
        'dead': ch.dead,
        'cards': [{
            'type': cl.type,
            'name': cl.ui_meta.lookup[cl.type],
            'cards': [card(c) for c in cl],
        } for cl in ch.lists if cl.type != 'special'] if extra else None,
        'tags': get_display_tags(ch) if extra else None,

        'name': m.name,
        'portrait': m.port_image,
        'figure': m.figure_image,
        'desc': m.char_desc(ch),
    }


def character_cls(cls) -> CharacterTypeView:
    m = cls.ui_meta
    return {
        'type': cls.__name__,
        'life': cls.life,
        'maxlife': cls.maxlife,
        'name': m.name,
        'portrait': m.port_image,
        'figure': m.figure_image,
        'desc': m.char_desc(cls),
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

    p = None
    for ch in g.players:
        if ch.player is me:
            p = ch
        chs.append(character(ch))

    assert p

    return {
        'characters': chs,
        'deck_remaining': len(g.deck.cards),
        'my_pid': me.pid,
        'my_skills': [
            skill(sk) for sk in p.skills
            if not getattr(sk, 'no_display', False)
        ],
    }
