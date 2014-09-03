# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import card_desc
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.shikieiki)


class Trial:
    # Skill
    name = u'审判'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class TrialAction:
    def effect_string(act):
        return u'幻想乡各地巫女妖怪纷纷表示坚决拥护|G【%s】|r将|G【%s】|r的判定结果修改为%s的有关决定！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            card_desc(act.card)
        )


class Majesty:
    # Skill
    name = u'威严'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MajestyAction:
    def effect_string(act):
        return u'|G【%s】|r脸上挂满黑线，收走了|G【%s】|r的一张牌填补自己的|G威严|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class TrialHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【审判】吗？'

    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'有罪！')
        else:
            return (False, u'请选择一张牌代替当前的判定牌')


class MajestyHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【威严】吗？'


class Shikieiki:
    # Character
    char_name = u'四季映姬'
    port_image = gres.shikieiki_port
    description = (
        u'|DB胸不平何以平天下 四季映姬 体力：3|r\n\n'
        u'|G审判|r：在任意角色的判定牌生效前，你可以打出一张牌代替之。\n\n'
        u'|G威严|r：可以立即从对你造成伤害的来源处获得一张牌。\n\n'
        u'|DB（画师：Pixiv UID 409282）|r'
    )
