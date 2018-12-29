# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbfaith
from thb.meta.common import ui_meta


# -- code --
@ui_meta(thbfaith.THBattleFaith)
class THBattleFaith:
    name = '信仰争夺战'
    logo = 'thb-modelogo-faith'
    description = (
        '|R游戏人数|r：6人\n'
        '\n'
        '|G游戏开始|r：游戏开始时，随机向在场玩家分配6张身份牌：3|!B博丽|r，3|!O守矢|r，双方对立。若出现同一方阵营座次连续三人的情况，则第三人须与下一名座次的玩家交换身份牌。\n'
        '\n'
        '|G选将阶段|r：共发给每人4张角色牌，其中一张为暗置。每名玩家选择其中一张作为出场角色，再选择一张作为备用角色（不得查看暗置角色牌）。将三张备用角色牌置于一旁作为备用角色。\n'
        '\n'
        '|G游戏开始|r：游戏开始时，所有角色摸4张牌，此时除首先行动的玩家均可以进行一次弃置4张牌并重新摸4张牌的操作。\n'
        '\n'
        '|G玩家死亡|r：当一名玩家死亡时，该玩家需弃置其所有的牌，然后弃置该玩家全部区域内的牌。从剩余的备用角色中选择一名作为出场角色并明示之，之后摸4张牌。此时该角色可以弃置全部的4张牌并重新摸4张牌。玩家死亡不执行任何奖惩。\n'
        '\n'
        '|G胜负条件|r：当一方死亡角色数到达三名，或投降时，该方判负。'
    )
    params_disp = {
        'random_seat': {
            'desc': '随机座位阵营',
            'options': [
                ('随机', True),
                ('固定', False),
            ],
        },
    }

    roles_disp = {
        thbfaith.THBFaithRole.HIDDEN: '？',
        thbfaith.THBFaithRole.HAKUREI: '博丽',
        thbfaith.THBFaithRole.MORIYA: '守矢',
    }


@ui_meta(thbfaith.DeathHandler)
class DeathHandler:
    # choose_option
    choose_option_buttons = (('全部换走', True), ('不用换', False))
    choose_option_prompt  = '你要将摸到的牌全部换掉吗？'
