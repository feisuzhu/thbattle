# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import OrderedDict

# -- third party --
# -- own --
from thb import thb2v2
from thb.ui.ui_meta.common import gen_metafunc


# -- code --
__metaclass__ = gen_metafunc(thb2v2)


class THBattle2v2:
    name = u'2v2模式'
    logo = 'thb-modelogo-2v2'
    description = (
        u'|R游戏人数|r：4人\n'
        u'\n'
        u'|G座次|r：\n'
        u'创建房间时可选固定阵容或随机阵容。\n'
        u'Roll点，由点数最高的玩家为1号位，然后对面点数最大的为2号位，按1-2-2-1的顺序逆时针行动。\n'
        u'\n'
        u'|G选将|r：\n'
        u'从角色堆里选出20名角色，由1号位开始，每人选择Ban掉其中一个角色。\n'
        u'每人随机从剩下的卡牌中获得4张角色卡作为备选（其中一张为阿卡林）\n'
        u'玩家可以选择其中一名角色进行游戏\n'
        u'\n'
        u'|G行动和胜利条件|r：\n'
        u'选择角色完毕后，每人摸4张牌。由一号位开始逆时针行动。\n'
        u'一名角色阵亡后，队友可以选择获得其所有牌或摸两张牌。\n'
        u'当一方所有的角色都阵亡时，游戏结束，另一方获胜。\n'
    )

    params_disp = OrderedDict((
        ('random_force', {
            'desc': u'随机阵营',
            'options': [
                (u'随机', True),
                (u'固定', False),
            ],
        }),
        ('draw_extra_card', {
            'desc': u'摸牌数量',
            'options': [
                (u'2张', False),
                (u'3张', True),
            ],
        }),
    ))

    def ui_class():
        from thb.ui.view import THBattle2v2UI
        return THBattle2v2UI

    T = thb2v2.Identity.TYPE
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


class HeritageHandler:
    # choose_option
    choose_option_buttons = ((u'获取队友的所有牌', 'inherit'), (u'摸两张牌', 'draw'))
    choose_option_prompt  = u'队友被击坠，请选择你的动作'
