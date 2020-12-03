# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbnewbie
from thb.meta.common import ui_meta, UIMetaBare


# -- code --
@ui_meta(thbnewbie.THBattleNewbie)
class THBattleNewbie(UIMetaBare):
    name = '琪露诺的完美THB教室'
    logo = 'thb-modelogo-newbie'
    description = (
        '|R游戏人数|r：1人+1NPC。\n'
        '\n'
        '|G游戏目标|r：让琪露诺带你飞。\n'
        '\n'
        '|G胜利条件|r：完整地完成教学，不掉线。\n'
        '\n'
    ).strip()

    roles = {
        'HIDDEN': {'name': '？',   'sprite': 'role-hidden'},
        'BAKA':   {'name': '笨蛋', 'sprite': 'role-baka'},
        'NEWBIE': {'name': '萌新', 'sprite': 'role-newbie'},
    }
