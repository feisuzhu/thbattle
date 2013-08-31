# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.sanae)


class Sanae:
    # Character
    char_name = u'东风谷早苗'
    port_image = gres.sanae_port
    description = (
        u'|DB常识满满的现人神 东风谷早苗 体力：3|r\n\n'
        u'|G御神签|r：出牌阶段，你可以指定一名其他角色，然后让其摸取等同于其残机数与场上残机数最多的角色的残机数之差的牌（至多4张，至少1张）。每阶段限一次。\n\n'
        u'|G奇迹|r：当你受到一次伤害，你可以指定任意一名角色摸X张牌（X为你已损失的体力值）。'
    )


class DrawingLotAction:
    def effect_string(act):
        return u'大吉！|G【%s】|r脸上满满的满足感，摸了%d张牌。' % (
            act.target.ui_meta.char_name,
            act.amount,
        )


class DrawingLot:
    name = u'御神签'

    def clickable(g):
        if my_turn() and not limit1_skill_used('drawinglot_tag'):
            return True

        return False

    def effect_string(act):
        return u'|G【%s】|r给|G【%s】|r抽了一签……' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌！')

        return (True, u'一定是好运气的！')


class Miracle:
    # Skill
    name = u'奇迹'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MiracleAction:
    def effect_string(act):
        return u'|G【%s】|r说，要有|G奇迹|r，于是|G【%s】|r就摸了%d张牌。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.amount,
        )


class MiracleHandler:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'奇迹：请选择1名其他玩家')

        return (True, u'奇迹！')
