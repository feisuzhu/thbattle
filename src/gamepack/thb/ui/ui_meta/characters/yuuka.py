# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn, build_handcard
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.yuuka)


class FlowerQueen:
    # Skill
    name = u'花王'

    def clickable(game):
        me = game.me
        if my_turn():
            return False

        if not (me.cards or me.showncards):
            return False

        try:
            act = game.action_stack[-1]
            return act.cond([build_handcard(cards.AttackCard)])
        except:
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择1张牌！')

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


class ReversedScales:
    # Skill
    name = u'逆鳞'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Sadist:
    # Skill
    name = u'抖Ｓ'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ReversedScalesAction:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r：“来正面上我啊！”'
        ) % (
            act.target.ui_meta.char_name,
        )


class SadistAction:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r又看了看|G【%s】|r：“你也要尝试一下么！”'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class SadistHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'发动【抖Ｓ】')
        else:
            return (False, u'【抖Ｓ】：请弃置一张牌')

    def target(pl):
        if not pl:
            return (False, u'【抖Ｓ】：请选择1名玩家')

        return (True, u'发动【抖Ｓ】')


class ReversedScalesHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【逆鳞】吗？'


class Yuuka:
    # Character
    char_name = u'风见幽香'
    port_image = gres.yuuka_port
    description = (
        u'|DB四季的鲜花之主 风见幽香 体力：4|r\n\n'
        u'|G逆鳞|r：其他角色对你使用的单体非延时符卡，你可以将其视为|G弹幕战|r。\n\n'
        u'|G花王|r：在你的回合外，你可以将任意一张手牌当做|G弹幕|r使用或打出。\n\n'
        u'|G抖Ｓ|r：当你击坠一名角色时，你可以弃置一张手牌并指定与其距离为1的一名其他角色；该角色被击坠后，你对指定的角色造成2点伤害。\n\n'
        u'|RKOF不平衡角色'
    )
