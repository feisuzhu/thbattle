# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, TYPE_CHECKING, cast
import itertools

# -- third party --
from typing_extensions import TypedDict

# -- own --
from thb.actions import PlayerTurn
from thb.mode import THBattle

# -- typing --
if TYPE_CHECKING:
    from thb.characters.base import Character  # noqa: F401


# -- code --
tags = {}


def ui_meta(f):
    tags[f.__name__] = f
    return f


class TagAnimation(TypedDict):
    sprite: str
    desc: str


def get_display_tags(g: THBattle, ch: Character) -> List[TagAnimation]:
    from thb.actions import ttags

    rst: List[TagAnimation] = []

    for t, v in itertools.chain(ch.tags.items(), ttags(ch).items()):
        meta = tags.get(t)
        if not meta:
            continue

        desc = meta(g, ch, v)
        if not desc:
            continue

        sprite, s = desc
        if sprite:
            assert isinstance(sprite, str)
            assert isinstance(s, str)
            rst.append({
                'sprite': sprite,
                'desc': s,
            })

    for c in ch.fatetell:
        rst.append({
            'sprite': cast(str, c.ui_meta.tag),
            'desc': cast(str, c.ui_meta.description),
        })

    return rst


@ui_meta
def vitality(g, p, v):
    try:
        current = PlayerTurn.get_current(g).target
    except IndexError:
        return None
    if v <= 0 and current is p:
        return 'thb-tag-attacked', '没有干劲了……'


@ui_meta
def wine(g, p, v):
    return v and ('thb-tag-wine', '喝醉了…')


@ui_meta
def flan_cs(g, p, v):
    try:
        current = PlayerTurn.get_current(g).target
    except IndexError:
        return None
    if v >= p.tags['turn_count'] and current is p:
        return 'thb-tag-flandrecs', '玩坏你哦！'


@ui_meta
def lunadial(g, p, v):
    try:
        current = PlayerTurn.get_current(g).target
    except IndexError:
        return None
    if v and current is p:
        return 'thb-tag-lunadial',  '咲夜的时间！'


@ui_meta
def riverside_target(g, p, v):
    if v == g.turn_count:
        return 'thb-tag-riverside', '被指定为彼岸的目标'


@ui_meta
def ran_ei(g, p, v):
    if v < p.tags['turn_count'] + 1:
        return 'thb-tag-ran_ei', '还可以发动极智'


@ui_meta
def aya_count(g, p, v):
    try:
        current = PlayerTurn.get_current(g).target
    except IndexError:
        return None
    if v >= 2 and p is current:
        return 'thb-tag-aya_range_max',  '使用卡牌时不受距离限制'


@ui_meta
def exterminate(g, p, v):
    return v and 'thb-tag-flandre_exterminate', '毁灭：无法使用人物技能'


@ui_meta
def reisen_discarder(g, p, v):
    return v and 'thb-tag-reisen_discarder', '丧心：下一个出牌阶段只能使用弹幕，且只能对最近的角色使用弹幕'


@ui_meta
def shizuha_decay(g, p, v):
    return v and 'thb-tag-shizuha_decay', '凋零：弃牌阶段需额外弃置一张手牌'


@ui_meta
def scarlet_mist(g, p, v):
    if v == 'buff':
        return 'thb-tag-scarlet_mist', '红雾：增益效果'


@ui_meta
def keine_devour(g, p, v):
    try:
        current = PlayerTurn.get_current(g).target
    except IndexError:
        return None
    if v and p is current:
        return 'thb-tag-keine_devour', '这位玩家的历史将会被慧音吞噬'


@ui_meta
def devoted(g, p, v):
    return 'thb-tag-keine_devoted', '合格的CP当然要同富贵共患难！'

# -----END TAGS UI META-----
