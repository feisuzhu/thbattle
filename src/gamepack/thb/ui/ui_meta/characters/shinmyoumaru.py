# -*- coding: utf-8 -*-

# -- stdlib --
import random

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

    def sound_effect(act):
        return random.choice((
            'thb-cv-shinmyoumaru_mallet1',
            'thb-cv-shinmyoumaru_mallet2',
        ))


class VengeOfTsukumogami:
    # Skill
    name = u'付丧神之怨'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VengeOfTsukumogamiAction:
    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G付丧神之怨|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return random.choice((
            'thb-cv-shinmyoumaru_venge1',
            'thb-cv-shinmyoumaru_venge2',
        ))


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
    miss_sound_effect = 'thb-cv-shinmyoumaru_miss'
    description = (
        u'|DB进击的小人 少名针妙丸 体力：4|r\n\n'
        u'|G付丧神之怨|r：当一名其他角色装备区的牌（因使用或打出以外的原因）直接进入弃牌堆后，你可以进行一次判定，若结果为9~K，你对其造成一点伤害。\n\n'
        u'|G万宝槌|r：在一名角色的判定牌生效前，你可以用一张点数大于此牌的牌替换之。\n\n'
        u'|DB（人物设计：yourccz95，CV：小羽）|r'
    )
