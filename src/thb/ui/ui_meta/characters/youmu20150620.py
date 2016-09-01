# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.youmu20150620)


class Youmu20150620:
    # Character
    name        = u'魂魄妖梦'
    title       = u'苍天型半人半灵'
    designer    = u'真炎的爆发'

    port_image        = u'thb-portrait-youmu20150620'


class Xianshizhan:
    # Skill
    name = u'现世斩'
    description = u'结束阶段开始时，你可以重铸1张非基本牌，视为对一名其他角色使用了1张|G弹幕|r'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class XianshizhanAttackCard:
    name = u'现世斩'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r对|G【%s】|r使用了|G现世斩|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class XianshizhanHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'现世斩!')
        else:
            return (False, u'现世斩：请选择一张非基本牌（否则不发动）')

    def target(pl):
        if not pl:
            return (False, u'现世斩：请选择1名玩家')

        return (True, u'现世斩!')


# -------------------------

class Jiongyanjian:
    # Skill
    name = u'炯眼剑'
    description = u'你可以对自己使用1张武器牌，视为使用或打出了1张|G擦弹|r；|B锁定技|r，当你响应|G弹幕|r后，若你有武器牌，你对使用者造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class JiongyanjianGrazeAction:
    def effect_string_before(act):
        return u'妖梦发动了|G炯眼剑|r'
