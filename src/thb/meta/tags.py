# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import itertools

# -- third party --
# -- own --
from thb.actions import PlayerTurn


# -- code --
tags = {}


def ui_meta(cls):
    tags[cls.__name__] = cls()
    return cls


def get_display_tags(p):
    from thb.actions import ttags

    rst = []

    try:
        for t, v in itertools.chain(p.tags.items(), ttags(p).items()):
            meta = tags.get(t)
            if not meta:
                continue

            desc = meta.desc(p, v)
            if not desc:
                continue

            rst.append(desc)

        for c in list(getattr(p, 'fatetell', ())):
            rst.append((c.ui_meta.tag_desc(c), c.ui_meta.description))

    except AttributeError:
        pass

    return rst


@ui_meta
class vitality:
    def desc(g, p, v):
        current = PlayerTurn.get_current(g).target
        if v <= 0 and current is p:
            return 'thb-tag-attacked', '没有干劲了……'


@ui_meta
class wine:
    def desc(g, p, v):
        return v and ('thb-tag-wine', '喝醉了…')


@ui_meta
class flan_cs:
    def desc(g, p, v):
        current = PlayerTurn.get_current(g).target
        if v >= p.tags['turn_count'] and current is p:
            return 'thb-tag-flandrecs', '玩坏你哦！'


@ui_meta
class lunadial:
    def desc(g, p, v):
        current = PlayerTurn.get_current(g).target
        if v and current is p:
            return 'thb-tag-lunadial',  '咲夜的时间！'


@ui_meta
class riverside_target:
    def desc(g, p, v):
        if v == g.turn_count:
            return 'thb-tag-riverside', '被指定为彼岸的目标'


@ui_meta
class ran_ei:
    def desc(g, p, v):
        if v < p.tags['turn_count'] + 1:
            return 'thb-tag-ran_ei', '还可以发动极智'


@ui_meta
class aya_count:
    def desc(g, p, v):
        current = PlayerTurn.get_current(g).target
        if v >= 2 and p is current:
            return 'thb-tag-aya_range_max',  '使用卡牌时不受距离限制'


@ui_meta
class exterminate:
    def desc(g, p, v):
        return v and 'thb-tag-flandre_exterminate', '毁灭：无法使用人物技能'


@ui_meta
class reisen_discarder:
    def desc(g, p, v):
        return v and 'thb-tag-reisen_discarder', '丧心：下一个出牌阶段只能使用弹幕，且只能对最近的角色使用弹幕'


@ui_meta
class shizuha_decay:
    def desc(g, p, v):
        return v and 'thb-tag-shizuha_decay', '凋零：弃牌阶段需额外弃置一张手牌'


@ui_meta
class scarlet_mist:
    def desc(g, p, v):
        if v == 'buff':
            return 'thb-tag-scarlet_mist', '红雾：增益效果'


@ui_meta
class keine_devour:
    def desc(g, p, v):
        current = PlayerTurn.get_current(g).target
        if v and p is current:
            return 'thb-tag-keine_devour', '这位玩家的历史将会被慧音吞噬'

# -----END TAGS UI META-----
