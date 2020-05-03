# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, cards, characters
from thb.ui.ui_meta.common import G, gen_metafunc, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.sp_youmu)


class SpYoumu:
    # Character (en.touhouwiki.net/wiki/Youmu_Konpaku#Skills)
    name        = u'苍天妖梦'
    title       = u'精益求精的庭师'
    illustrator = u'暂缺'
    designer    = u'真炎的爆发'
    cv          = u'小羽'

    port_image  = u'thb-portrait-youmu20150620'


class PresentWorldSlash:
    # Skill
    name = u'现世'
    description = u'出牌阶段结束时，若你没有干劲，你可以将一张牌当|G弹幕|r使用。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G现世|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-youmu_mjchz'


class PresentWorldSlashAction:

    def effect_string(act):
        return u'（现世发动后相关描写）'

    # no effect string, for skill wrap has it; if put here, double strings in game info
    def sound_effect(act):
        return 'thb-cv-card_attack2'


class PresentWorldSlashHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'发动现世斩!')
        else:
            return (False, u'现世：请选择一张牌（否则不发动）')

    def target(pl):
        if not pl:
            return (False, u'现世：请选择一名其它角色')

        return (True, u'现世斩!')


# -------------------------

class InsightfulSword:
    # Skill
    name = u'炯眼'
    description = u'你可以对自己使用一张武器牌，视为使用或打出一张|G擦弹|r；若你以此方式响应的是|G弹幕|r效果，在抵消该效果后，你对其发动者造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class InsightfulSwordGrazeAction:

    def effect_string(act):
        return u'|G【%s】|r发动了|G炯眼|r。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-youmu_nitoryuu'


class InsightfulSwordDamageAction:

    def effect_string(act):
        return u'（剑斩弹幕+反伤动作描写）'

    def sound_effect(act):
        return ''


class InsightfulSwordGrazeCard:

    # Card Virtual but name displayed in UseCard
    name = u'炯眼'

    def effect_string(act):
        return u'（炯眼+突然拔剑动作描写）'

    def sound_effect(act):
        if not isinstance(act, actions.LaunchCard):
            return 'thb-cv-card_graze2'

        current = G().current_player
        if act.source is not current:
            return 'thb-cv-card_graze3'
