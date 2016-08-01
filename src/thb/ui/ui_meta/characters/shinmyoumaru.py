# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.shinmyoumaru)


class MiracleMallet:
    # Skill
    name = u'万宝槌'
    description = u'当一名角色的判定牌生效前，你可以用一张点数大于此牌的牌替换之。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MiracleMalletAction:
    def effect_string(act):
        return u'|G【%s】|r将|G【%s】|r的判定结果改为%s。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
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
    description = u'每当其他角色装备区的牌因弃置而置入弃牌堆时，你可以进行一次判定，若为9~K，你对其造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VengeOfTsukumogamiAction:
    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G付丧神之怨|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
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
        return prompt % act.target.ui_meta.name


class Shinmyoumaru:
    # Character
    name        = u'少名针妙丸'
    title       = u'进击的小人'
    illustrator = u'六仔OwO'
    designer    = u'yourccz95'
    cv          = u'小羽'

    port_image        = u'thb-portrait-shinmyoumaru'
    figure_image      = u'thb-figure-shinmyoumaru'
    miss_sound_effect = u'thb-cv-shinmyoumaru_miss'
