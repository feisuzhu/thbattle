# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.yuuka)


class FlowerQueen:
    # Skill
    name = u'花王'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
            if isinstance(act, (cards.UseAttack, cards.BaseUseGraze, cards.DollControl)):
                return True
        except IndexError:
            pass
        return False

    def is_complete(g, cl):
        skill = cl[0]
        acards = skill.associated_cards
        if len(acards) != 1 or acards[0].suit != cards.Card.CLUB:
            return (False, u'请选择1张草花色牌！')
        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return None  # FIXME


class MagicCannon:
    # Skill
    name = u'魔炮'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MagicCannonAttack:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r已经做好了迎接弹幕的准备，谁知冲过来的竟是一束|G魔炮|r！'
        ) % (
            act.target.ui_meta.char_name,
        )


class PerfectKill:
    # Skill
    name = u'完杀'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class PerfectKillAction:
    def effect_string(act):
        return (
            u'在场的人无不被|G【%s】|r的气场镇住，竟连上前递|G麻薯|r的勇气都没有了！'
        ) % (
            act.source.ui_meta.char_name,
        )


class Yuuka:
    # Character
    char_name = u'风见幽香'
    port_image = gres.yuuka_port
    description = (
        u'|DB四季的鲜花之主 风见幽香 体力：3|r\n\n'
        u'|G花王|r：你的所有的梅花牌都可以当做【弹幕】和【擦弹】使用或打出。\n\n'
        u'|G魔炮|r：锁定技，你在使用红色的【弹幕】时伤害+1\n\n'
        u'|G完杀|r：锁定技，由你击杀的玩家只能由你的和被击杀玩家的【麻薯】救起。'
    )
