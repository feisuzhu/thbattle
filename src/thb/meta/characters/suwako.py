# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --


# -- code --
@ui_meta(characters.suwako.Divine)
class Divine:
    # Skill
    # 做一点微小的工作
    name = '神御'
    description = '准备阶段开始时，你可以获得一名与你距离2以内角色的一张手牌；若如此做，你的弃牌阶段结束后，该角色从你的弃牌中获得一张牌。'


@ui_meta(characters.suwako.DivineFetchHandler)
class DivineFetchHandler:
    def target(self, pl):
        if not pl:
            return (False, '<style=Skill.Name>神御</style>：请选择1名玩家（可取消）')

        return (True, '<style=Skill.Name>神御</style>：获得该角色的1张手牌')


@ui_meta(characters.suwako.DivineFetchAction)
class DivineFetchAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}发动了<style=Skill.Name>神御</style>。'

    def sound_effect(self, act):
        return ''


@ui_meta(characters.suwako.DivinePickAction)
class DivinePickAction:
    # string to modify: it can work and it shall include name of target (possessing Divine)
    def effect_string(self, act):
        c = getattr(act, 'card', None)
        src = act.source
        return c or f'{N.char(src)}获得了{N.card(c)}。'

    def sound_effect(self, act):
        return ''


@ui_meta(characters.suwako.SpringSign)
class SpringSign:
    # Skill
    # 闷声发大财
    name = '丰源'
    description = '<style=B>锁定技</style>，你的出牌阶段结束时，你摸两张牌。'


@ui_meta(characters.suwako.SpringSignDrawCards)
class SpringSignDrawCards:
    def effect_string(self, act):
        # needed > _ <
        return '（丰源效果台词）'

    def sound_effect(self, act):
        return ''


@ui_meta(characters.suwako.Suwako)
class Suwako:
    # Character
    name        = '洩矢诹访子'
    title       = '小小青蛙不输风雨'
    illustrator = '六仔OwO'
    cv          = '暂缺'

    # 这都是历史的进程啊
    miss_sound_effect = ''
