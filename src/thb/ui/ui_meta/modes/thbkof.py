# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thbkof
from thb.ui.ui_meta.common import gen_metafunc


# -- code --
__metaclass__ = gen_metafunc(thbkof)


class THBattleKOF:
    name = u'KOF模式'
    logo = 'thb-modelogo-kof'
    description = (
        u'|R游戏人数|r：2人。\n'
        u'\n'
        u'|R角色选择|r：从ROLL点更高的玩家开始，按照1-2-2-2-2-1进行角色选择。\n'
        u'\n'
        u'|R游戏过程|r：选好角色后，将会翻开第一个角色进行对决，其他角色为隐藏。当有一方角色被击坠后，需弃置全部区域内的所有牌（手牌、装备区的牌、判定区的牌），然后选择下一个出场的角色，并摸4张牌。\n'
        u'\n'
        u'|R胜利条件|r：当其中一方3名角色被击坠时，判对方胜出。'
    )

    params_disp = {
    }

    def ui_class():
        from thb.ui.view import THBattleKOFUI
        return THBattleKOFUI

    T = thbkof.Identity.TYPE
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
