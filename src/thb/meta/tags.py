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
                'desc': s,
            })

    for c in ch.fatetell:
        rst.append({
            'sprite': cast(str, c.ui_meta.tag),
            'desc': cast(str, c.ui_meta.description),
        })

    return rst


@ui_meta
def vitality(p, v):
    return v and ('thb-tag-attacked', '没有干劲了……')


@ui_meta
def wine(p, v):
    return v and ('thb-tag-wine', '喝醉了…')


@ui_meta
def flan_cs(p, v):
    return v and ('thb-tag-flandrecs', '玩坏你哦！')


@ui_meta
def lunadial(p, v):
    return v and ('thb-tag-lunadial',  '咲夜的时间！')


@ui_meta
def riverside_target(p, v):
    return v and ('thb-tag-riverside', '被指定为彼岸的目标')


@ui_meta
def ran_ei(p, v):
    if v < p.tags['turn_count'] + 1:
        return 'thb-tag-ran_ei', '还可以发动极智'


@ui_meta
def aya_count(p, v):
    return ('thb-tag-aya_range_max',  '使用卡牌时不受距离限制') if v >= 2 else None


@ui_meta
def exterminate(p, v):
    return v and 'thb-tag-flandre_exterminate', '毁灭：无法使用人物技能'


@ui_meta
def reisen_discarder(p, v):
    return v and 'thb-tag-reisen_discarder', '丧心：下一个出牌阶段只能使用弹幕，且只能对最近的角色使用弹幕'


@ui_meta
def shizuha_decay(p, v):
    return v and 'thb-tag-shizuha_decay', '凋零：弃牌阶段需额外弃置一张手牌'


@ui_meta
def scarlet_mist(p, v):
    return ('thb-tag-scarlet_mist', '红雾：增益效果') if v == 'buff' else None


@ui_meta
def devoted(p, v):
    return 'thb-tag-keine_devoted', '合格的CP当然要同富贵共患难！'

# -----END TAGS UI META-----
