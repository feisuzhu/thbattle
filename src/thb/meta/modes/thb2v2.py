# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thb2v2
from thb.meta.common import ui_meta


# -- code --
@ui_meta(thb2v2.THBattle2v2)
class THBattle2v2:
    name = '2v2模式'
    logo = 'thb-modelogo-2v2'
    description = (
        '|R游戏人数|r：4人\n'
        '\n'
        '|G座次|r：\n'
        '创建房间时可选固定阵容或随机阵容。\n'
        'Roll点，由点数最高的玩家为1号位，然后对面点数最大的为2号位，按1-2-2-1的顺序逆时针行动。\n'
        '\n'
        '|G选将|r：\n'
        '从角色堆里选出20名角色，由1号位开始，每人选择Ban掉其中一个角色。\n'
        '每人随机从剩下的卡牌中获得4张角色卡作为备选（其中一张为阿卡林）\n'
        '玩家可以选择其中一名角色进行游戏\n'
        '\n'
        '|G行动和胜利条件|r：\n'
        '选择角色完毕后，每人摸4张牌。由一号位开始逆时针行动。\n'
        '一名角色阵亡后，队友可以选择获得其所有牌或摸两张牌。\n'
        '当一方所有的角色都阵亡时，游戏结束，另一方获胜。\n'
    )

    params_disp = {
        'draw_extra_card': {
            'desc': '摸牌数量',
            'options': [('2张', False), ('3张', True)]
        },
        'random_force': {
            'desc': '随机阵营',
            'options': [('随机', True), ('固定', False)]
        }
    }

    roles_disp = {
        thb2v2.THB2v2Role.HIDDEN: '？',
        thb2v2.THB2v2Role.HAKUREI: '博丽',
        thb2v2.THB2v2Role.MORIYA: '守矢',
    }


@ui_meta(thb2v2.HeritageHandler)
class HeritageHandler:
    # choose_option
    choose_option_buttons = (('获取队友的所有牌', 'inherit'), ('摸两张牌', 'draw'))
    choose_option_prompt  = '队友被击坠，请选择你的动作'
