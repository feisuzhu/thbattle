# -*- coding: utf-8 -*-
# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.shinmyoumaru)


class MiracleMallet:
    # Skill
    name = u'万宝槌'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MiracleMalletAction:
    def effect_string(act):
        return u'|G【%s】|r将|G【%s】|r的判定结果改为%s。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            card_desc(act.card)
        )


class VengeOfTsukumogami:
    # Skill
    name = u'付丧神之怨'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VengeOfTsukumogamiAction:
    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G付丧神之怨|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class MiracleMalletHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'发动【万宝槌】！')
        else:
            return (False, u'请选择一张牌点数更大的牌代替当前的判定牌')


class VengeOfTsukumogamiHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))

    def choose_option_prompt(act):
        prompt = u'你要发动【付丧神之怨】吗（对%s）？'
        return prompt % act.target.ui_meta.char_name


class Shinmyoumaru:
    # Character
    char_name = u'少名针妙丸'
    port_image = 'thb-portrait-shinmyoumaru'
    description = (
        u'|DB小人的道路 少名针妙丸 体力：4|r\n\n'
        u'|G万宝槌|r：在一名角色的判定牌生效前，你可以打出一张点数大于该判定牌的牌代替。\n\n'
        u'|G付丧神之怨|r：当其他角色装备区的牌进入弃牌堆后，你可以令其做一次判定，若点数大于9则视为你对其使用一张弹幕。'
    )
