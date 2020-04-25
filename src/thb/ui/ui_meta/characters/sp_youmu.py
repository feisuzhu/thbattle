# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import build_handcard, gen_metafunc, passive_clickable, passive_is_action_valid


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
    description = u'出牌阶段结束后，若你没有干劲，你可以弃置一张牌，视为对你指定的一名其它角色使用一张|G弹幕|r。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class PresentWorldSlashAttackCard:
    name = u'现世'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r对|G【%s】|r使用了|G现世斩|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-youmu_mjchz'


class PresentWorldHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'使用现世斩!')
        else:
            return (False, u'现世斩：请选择一张牌（否则不发动）')

    def target(pl):
        if not pl:
            return (False, u'现世斩：请选择一名其它角色')

        return (True, u'现世斩!')


# -------------------------

class InsightfulSword:
    # Skill
    name = u'炯眼'
    description = u'你可以对自己使用一张武器牌，视为使用或打出一张|G擦弹|r；若你以此方式响应的是|G弹幕|r效果，在抵消该效果后，你对其发动者造成1点伤害。'

    def clickable(g):
        try:
            act = g.action_stack[-1]
            if act.cond([build_handcard(cards.GrazeCard)]):
                return True
        except:
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards

        if len(cl) != 1:
            return (False, u'炯眼：请选择一张牌（否则不发动）')
        elif cl[0].is_card(cards.VirtualCard):
            return (False, u'「炯眼」不允许组合使用')
        elif set(getattr(cl[0], 'category')) != {'equipment', 'weapon'}:
            return (False, u'炯眼：请务必选择一张武器牌！')

        return (True, u'才不要！！')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source

        # strings below are to be modified (> _ <)
        return (
            u'|G【%s】|r发动了|G炯眼|r！'
        ) % (
            source.ui_meta.name,
        )

    def sound_effect(act):
         return 'thb-cv-card_graze2'


class InsightfulSwordAction:
    def effect_string_before(act):
        # strings below are to be modified = =
        return u'|G【%s】|r的|G炯眼|r即将对|G【%s】|r造成伤害……' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-youmu_nitoryuu'
