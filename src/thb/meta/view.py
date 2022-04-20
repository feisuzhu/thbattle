# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, List, Optional, TypedDict, cast

# -- third party --
# -- own --
from client.base import ClientGameRunner
from thb.cards.base import VirtualCard
from thb.meta import view
from thb.meta.tags import TagAnimation, get_display_acqsktags, get_display_ctags
from thb.meta.tags import get_display_skatags, get_display_tags
from thb.mode import THBattle


# -- code --
class CardMetaView(TypedDict, total=False):
    type: str
    ptype: str
    suit: int
    number: int
    color: str
    sync_id: int
    track_id: int
    params: Optional[Dict[str, Any]]
    resides_in: Optional[str]
    owner: int
    # name: str
    # image: str
    # desc: Optional[str]
    # eqpcat: str


class CardListView(TypedDict):
    type: str
    name: str
    cards: List[CardMetaView]


def card(c, with_description=False) -> CardMetaView:
    # m = c.ui_meta
    if (l := c.resides_in) is not None:
        resides_in = l.type
        owner = l.owner.get_player().pid if l.owner else 0
    else:
        resides_in = None
        owner = 0

    cl = VirtualCard.unwrap([c])
    if len(cl) == 1:
        ptype = cl[0].__class__.__name__
    else:
        ptype = "Fallback"

    rst: CardMetaView = {
        'type': c.__class__.__name__,
        'ptype': ptype,  # Actual PhysicalCard type
        'suit': c.suit,
        'number': c.number,
        'color': c.color,
        'sync_id': c.sync_id,
        'track_id': c.track_id,
        'params': getattr(c, 'action_params', None),
        'resides_in': resides_in,
        'owner': owner,
    }

    return cast(CardMetaView, {k: v for k, v in rst.items() if v is not None})


# FIXME: merge this with CharacterView
class CharacterTypeView(TypedDict):
    type: str
    # maxlife: int
    name: str
    # portrait: str
    # figure: str
    # desc: str


class CharacterView(CharacterTypeView):
    pid: int
    life: int
    maxlife: int
    dead: bool
    cards: List[CardListView]
    tags: List[TagAnimation]       # Tags;
    acqsktags: List[TagAnimation]  # AcquiredSkillTags;
    skatags: List[TagAnimation]    # SkillAvailabilityTags;
    ctags: List[TagAnimation]      # CardTags;
    drunk: bool


def character(ch) -> CharacterView:
    m = ch.ui_meta
    return {
        'pid': ch.player.pid,
        'type': ch.__class__.__name__,
        'name': m.name,
        'life': ch.life,
        'maxlife': ch.maxlife,  # maxlife is an instance variable! DO NOT OMIT!
        'dead': ch.dead,
        'cards': [{
            'type': cl.type,
            'name': cl.ui_meta.lookup[cl.type],
            'cards': [card(c) for c in cl],
        } for cl in ch.lists if cl.type != 'special'],
        'tags': get_display_tags(ch),
        'acqsktags': get_display_acqsktags(ch),
        'skatags': get_display_skatags(ch),
        'ctags': get_display_ctags(ch),
        'drunk': bool(ch.tags['wine']),
    }


def character_cls(cls) -> str:
    return cls.__name__

    # m = cls.ui_meta
    # return {
    #     'type': cls.__name__,
    #     'maxlife': cls.maxlife,
    #     'name': m.name,
    #     'portrait': m.port_image,
    #     'figure': m.figure_image,
    #     'desc': m.char_desc(cls),
    # }


class SkillView(TypedDict, total=False):
    type: str
    name: str
    # desc: str
    # skcat: List[str]
    # ui: str
    clickable: bool


def skill(g, sk) -> SkillView:
    runner = g.runner
    assert isinstance(runner, ClientGameRunner)
    in_user_input = runner.in_user_input
    return {
        'type': sk.__name__,
        # 'name': m.name,
        # 'skcat': sk.skill_category,
        # 'ui': getattr(sk, 'params_ui', None),
        'clickable': in_user_input and sk.ui_meta.clickable(),
    }


class GameState(TypedDict):
    characters: List[view.CharacterView]
    deck_remaining: int
    my_pid: int
    my_skills: List[view.SkillView]


def state_of(g: THBattle) -> Optional[GameState]:
    try:
        players = g.players
        deck = g.deck
    except AttributeError:
        return None

    runner = g.runner
    assert isinstance(runner, ClientGameRunner)
    core = runner.core
    chs: List[view.CharacterView] = []
    me = core.game.theone_of(g)

    p = None
    for ch in players:
        if ch.get_player() is me:
            p = ch
        chs.append(character(ch))

    skills = [skill(g, sk) for sk in p.skills] if p else []

    return {
        'characters': chs,
        'deck_remaining': len(deck.cards),
        'my_pid': me.pid,
        'my_skills': skills,
    }
