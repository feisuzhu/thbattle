# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.momiji)


class Momiji:
    # Character
    char_name = u'犬走椛'
    port_image = gres.momiji_port
    description = (
        u'|DB山中的千里眼 犬走椛 体力：4|r\n\n'
        u'|G哨戒|r：当其他玩家（记作A）使用弹幕并对另一玩家（记作B）造成伤害时，若A在你的攻击距离内，你可以使用一张弹幕或梅花色牌作为弹幕对A使用。若此弹幕造成伤害，你可以防止此伤害，并且使B受到的伤害-1。\n\n'
        u'|G千里眼|r：你与其他玩家结算距离时始终-1\n\n'
        u'|DB（画师：Danbooru post 621700）|r'
    )


class Sentry:
    # Skill
    name = u'哨戒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SharpEye:
    # Skill
    name = u'千里眼'
    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SentryAttack:
    # Skill
    name = u'哨戒'


class SentryHandler:
    # choose_option meta
    choose_option_buttons = ((u'保护', True), (u'伤害', False))
    choose_option_prompt = u'你希望发动的效果？'

    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'吃我大弹幕啦！(对%s发动哨戒)' % act.target.ui_meta.char_name)
        else:
            return (False, u'请选择一张弹幕或者草花色牌发动哨戒(对%s)' % act.target.ui_meta.char_name)
