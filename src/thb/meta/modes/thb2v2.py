# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thb2v2
from thb.meta.common import ui_meta, UIMetaBare


# -- code --
@ui_meta(thb2v2.THBattle2v2)
class THBattle2v2(UIMetaBare):
    name = '2v2模式'
    logo = 'thb-modelogo-2v2'
    description = (
        '<style=B>座次</style>：\n'
        '创建房间时可选固定阵容或随机阵容。\n'
        'Roll点，由点数最高的玩家为1号位，然后对面点数最大的为2号位，按1-2-2-1的顺序逆时针行动。\n'
        '\n'
        '<style=B>角色选择</style>：\n'
        '从角色堆里选出20名角色，由1号位开始，每人选择BAN掉其中一个角色。\n'
        '每人随机从剩下的卡牌中获得4张角色卡作为备选（其中一张为阿卡林）。\n'
        '玩家可以选择其中一名角色进行游戏。\n'
        '\n'
        '<style=B>行动和胜利条件</style>：\n'
        '选择角色完毕后，每人摸4张牌。由一号位开始逆时针行动。\n'
        '一名角色被击坠后，队友可以选择获得其所有牌或摸两张牌。\n'
        '当一方所有的角色都被击坠时，游戏结束，另一方获胜。\n'
    )

    params = {
        'draw_extra_card': [
            ('正常摸牌', False),
            ('摸3张牌', True),
        ],
        'random_force': [
            ('随机阵营', True),
            ('固定阵营', False),
        ]
    }

    roles = {
        'HIDDEN':  {'name': '？',   'sprite': 'role-hidden'},
        'HAKUREI': {'name': '博丽', 'sprite': 'role-hakurei'},
        'MORIYA':  {'name': '守矢', 'sprite': 'role-moriya'},
    }


@ui_meta(thb2v2.HeritageHandler)
class HeritageHandler:
    # choose_option
    choose_option_buttons = (('获取队友的所有牌', 'inherit'), ('摸两张牌', 'draw'))
    choose_option_prompt  = '队友被击坠，请选择你的动作'
