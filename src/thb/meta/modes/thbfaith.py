# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbfaith
from thb.meta.common import ui_meta, UIMetaBare


# -- code --
@ui_meta(thbfaith.THBattleFaith)
class THBattleFaith(UIMetaBare):
    name = '信仰争夺战'
    logo = 'thb-modelogo-faith'
    description = (
        '<style=B>游戏开始</style>：游戏开始时，随机向在场玩家分配6张身份牌：3<sprite=Role.Hakurei>，3<sprite=Role.Moriya>，双方对立。若出现同一方阵营座次连续三人的情况，则第三人须与下一名座次的玩家交换身份牌。\n'
        '<style=B>角色选择</style>：共发给每人4张角色牌，其中一张为暗置。每名玩家选择其中一张作为出场角色，再选择一张作为备用角色（不得查看暗置角色牌）。每方阵营将三张备用角色牌置于一旁作为备用角色。\n'
        '<style=B>游戏开始</style>：游戏开始时，所有角色摸4张牌，此时除首先行动的玩家均可以进行一次弃置4张牌并重新摸4张牌的操作。\n'
        '<style=B>角色坠机</style>：当一名角色被击坠时，弃置该角色全部区域内的所有牌。从剩余的备用角色中选择一名作为出场角色并明示之，之后摸4张牌。此时该角色可以弃置全部的4张牌并重新摸4张牌。击坠不执行任何奖惩。\n'
        '<style=B>胜负条件</style>：当一方累计被击坠角色数到达三名，或投降时，该方判负。'
    )

    params = {
        'random_seat': [
            ('随机座位阵营', True),
            ('固定座位阵营', False),
        ],
    }

    roles = {
        'HIDDEN':  {'name': '？',   'sprite': 'role-hidden'},
        'HAKUREI': {'name': '博丽', 'sprite': 'role-hakurei'},
        'MORIYA':  {'name': '守矢', 'sprite': 'role-moriya'},
    }


@ui_meta(thbfaith.DeathHandler)
class DeathHandler:
    # choose_option
    choose_option_buttons = (('全部换走', True), ('不用换', False))
    choose_option_prompt  = '你要将摸到的牌全部换掉吗？'
