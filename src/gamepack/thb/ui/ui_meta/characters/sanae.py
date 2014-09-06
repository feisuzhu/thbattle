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
    miss_sound_effect = gres.cv.sanae_miss
    description = (
        u'|DB常识满满的现人神 东风谷早苗 体力：3|r\n\n'
        u'|G御神签|r：出牌阶段，你可以指定一名其他角色，然后让其摸取等同于其残机数与场上残机数最多的角色的残机数之差的牌（至多4张，至少1张）。每阶段限一次。\n\n'
        u'|G奇迹|r：当你受到一次【弹幕】的伤害后，你可以弃置X张牌（不足则全弃）然后摸X张牌。若你的体力为全场最少的角色或之一，你可以令一名其他角色也如此做。（X为你已损失的体力值）\n\n'
        u'|DB（画师：Pixiv ID 8684643，CV：VV）|r'
    )


class DrawingLotAction:
    def effect_string(act):
        return u'大吉！|G【%s】|r脸上满满的满足感，摸了%d张牌。' % (
            act.target.ui_meta.char_name,
            act.amount,
        )

    def sound_effect(act):
        return gres.cv.sanae_drawinglot


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
        return u'|G【%s】|r说，要有|G奇迹！' % (
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return gres.cv.sanae_miracle

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'奇迹：请选择1名其他玩家，执行相同的动作')

        return (True, u'奇迹！')

    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置这些牌，并摸%d张牌' % act.amount)
        else:
            return (False, u'请选择%d张牌弃置，并摸%d张牌' % (act.amount, act.amount))


class MiracleHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【奇迹】吗？'
