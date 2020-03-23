# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thbfaith
from thb.ui.ui_meta.common import gen_metafunc


# -- code --
__metaclass__ = gen_metafunc(thbfaith)


class THBattleFaith:
    name = u'信仰争夺战'
    logo = 'thb-modelogo-faith'
    description = (
        u'|R游戏人数|r：6人。\n'
        u'\n'
        u'|G游戏开始|r：游戏开始时，随机向在场玩家分配6张身份牌：3|!B博丽|r，3|!O守矢|r，双方对立。若出现同一方阵营座次连续三人的情况，则第三人须与下一名座次的玩家交换身份牌。\n'
        u'\n'
        u'|G角色选择|r：共发给每人4张角色牌，其中一张为暗置。每名玩家选择其中一张作为出场角色，再选择一张作为备用角色（不得查看暗置角色牌）。每方阵营将三张备用角色牌置于一旁作为备用角色。\n'
        u'\n'
        u'|G游戏开始|r：游戏开始时，所有角色摸4张牌，此时除首先行动的玩家均可以进行一次弃置4张牌并重新摸4张牌的操作。\n'
        u'\n'
        u'|G角色更新|r：当一名角色被击坠时，弃置该角色全部区域内的所有牌。从剩余的备用角色中选择一名作为出场角色并明示之，之后摸4张牌。此时该角色可以弃置全部的4张牌并重新摸4张牌。击坠不执行任何奖惩。\n'
        u'\n'
        u'|G胜负条件|r：当一方累计被击坠角色数到达三名，或投降时，该方判负。'
    )
    params_disp = {
        'random_seat': {
            'desc': u'随机座位阵营',
            'options': [
                (u'随机', True),
                (u'固定', False),
            ],
        },
    }

    def ui_class():
        from thb.ui.view import THBattleFaithUI
        return THBattleFaithUI

    T = thbfaith.Identity.TYPE
    identity_table = {
        T.HIDDEN:  u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA:  u'守矢'
    }

    identity_color = {
        T.HIDDEN:  u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA:  u'orange'
    }

    IdentityType = T
    del T


class DeathHandler:  # noqa
    # choose_option
    choose_option_buttons = ((u'全部换走', True), (u'不用换', False))
    choose_option_prompt  = u'你要将摸到的牌全部换掉吗？'
