# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, TYPE_CHECKING, TypedDict, cast
import itertools

# -- third party --
# -- own --

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
    gray: bool
    desc: str


def get_display_tags(ch: Character) -> List[TagAnimation]:
    from thb.actions import ttags

    rst: List[TagAnimation] = []

    for t, v in itertools.chain(ch.tags.items(), ttags(ch).items()):
        meta = tags.get(t)
        if not meta:
            continue

        desc = meta(ch, v)
        if not desc:
            continue

        sprite, s = desc
        if sprite:
            assert isinstance(sprite, str)
            assert isinstance(s, str)
            rst.append({
                'sprite': sprite,
                'gray': False,
                'desc': s,
            })

    return rst


def get_display_acqsktags(ch: Character) -> List[TagAnimation]:
    rst: List[TagAnimation] = []

    for sk in ch.skills:
        if 'acquired' in sk.skill_category:
            rst.append({
                'sprite': cast(str, sk.__name__),
                'gray': False,
                'desc': cast(str, sk.ui_meta.description),
            })

    return rst


def get_display_skatags(ch: Character) -> List[TagAnimation]:
    rst: List[TagAnimation] = []

    skills = set(ch.__class__.skills)
    skills.update(ch.skills)

    for sk in skills:
        if avail := getattr(sk.ui_meta, 'is_available', None):
            rst.append({
                'sprite': cast(str, sk.__name__),
                'gray': not avail(ch),
                'desc': cast(str, sk.ui_meta.description),
            })

    return rst


def get_display_ctags(ch: Character) -> List[TagAnimation]:
    rst: List[TagAnimation] = []

    for c in ch.fatetell:
        rst.append({
            'sprite': cast(str, c.ui_meta.tag),
            'gray': False,
            'desc': cast(str, c.ui_meta.description),
        })

    return rst


@ui_meta
def flan_cs(p, v):
    return v and ('flandre-cs', '玩坏你哦！')


@ui_meta
def lunadial(p, v):
    return v and ('lunadial',  '咲夜的时间！')


@ui_meta
def riverside_target(p, v):
    return v and ('riverside', '被指定为彼岸的目标')


@ui_meta
def aya_count(p, v):
    return ('aya-range-max',  '使用卡牌时不受距离限制') if v >= 2 else None


@ui_meta
def exterminate(p, v):
    return v and 'flandre-exterminate', '毁灭：无法使用人物技能'


@ui_meta
def shizuha_decay(p, v):
    return v and 'shizuha-decay', '凋零：弃牌阶段需额外弃置一张手牌'


@ui_meta
def scarlet_mist(p, v):
    if v == 'buff':
        return ('scarlet-mist-buff', '红雾：弹幕无视距离 & 回复体力')
    else:
        return ('scarlet-mist-nerf', '红雾：弹幕仅可以指定距离为1的目标')


@ui_meta
def shikigami_target(p, v):
    other = p.tags['shikigami_target']
    origin = p if 'shikigami_tag' in p.tags else other
    if origin.tags['shikigami_tag'] == origin.tags['turn_count']:
        return ('shikigami', '式神：共享攻击范围')


# -----END TAGS UI META-----
