# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thb3v3
from thb.ui.ui_meta.common import gen_metafunc


# -- code --
__metaclass__ = gen_metafunc(thb3v3)


class THBattle:
    name = u'3v3模式'
    logo = 'thb-modelogo-3v3'
    description = (
        u'|R游戏人数|r：6人。\n'
        u'\n'
        u'阵营分为|!B博丽|r和|!O守矢|r，每个阵营3名玩家，交错入座。\n'
        u'由ROLL点最高的人开始，按照顺时针1-2-2-1的方式选将。\n'
        u'选将完成由ROLL点最高的玩家开始行动。\n'
        u'ROLL点最高的玩家开局摸3张牌，其余玩家开局摸4张牌。\n'
        u'\n'
        u'|R胜利条件|r：击坠对方阵营所有角色。'
    )
    params_disp = {
        'random_seat': {
            'desc': u'随机座位阵营',
            'options': [
                (u'固定', False),
                (u'随机', True),
            ],
        },
    }

    def ui_class():
        from thb.ui.view import THBattleUI
        return THBattleUI

    T = thb3v3.Identity.TYPE
    identity_table = {
        T.HIDDEN: u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA: u'守矢'
    }

    identity_color = {
        T.HIDDEN: u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA: u'orange'
    }

    IdentityType = T
    del T
