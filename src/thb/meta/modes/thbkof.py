# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbkof
from thb.meta.common import ui_meta, UIMetaBare


# -- code --
@ui_meta(thbkof.THBattleKOF)
class THBattleKOF(UIMetaBare):
    name = 'KOF模式'
    logo = 'thb-modelogo-kof'
    description = (
        '<style=B>角色选择</style>：从ROLL点最高的玩家开始，按照1-2-2-2-2-1进行角色选择。\n'
        '<style=B>游戏过程</style>：选好角色后，将会翻开第一个角色进行对决，其他角色为隐藏。当有一方角色被击坠后，需弃置全部区域内的所有牌（手牌、装备区的牌、判定区的牌），然后选择下一个出场的角色，并摸4张牌。\n'
        '<style=B>胜利条件</style>：当其中一方3名角色被击坠时，判对方胜出。'
    )

    roles = {
        'HIDDEN':  {'name': '？',   'sprite': 'role-hidden'},
        'HAKUREI': {'name': '博丽', 'sprite': 'role-hakurei'},
        'MORIYA':  {'name': '守矢', 'sprite': 'role-moriya'},
    }

    params: dict = {}
