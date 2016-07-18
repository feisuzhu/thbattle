# -*- coding: utf-8 -*-
# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.shikieiki)


class Trial:
    # Skill
    name = u'审判'
    description = u'在一名角色的判定牌生效前，你可以打出一张牌代替之。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class TrialAction:
    def effect_string(act):
        return u'幻想乡各地巫女妖怪纷纷表示坚决拥护|G【%s】|r将|G【%s】|r的判定结果修改为%s的有关决定！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card)
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-shikieiki_trial1',
            'thb-cv-shikieiki_trial2',
        ])


class Majesty:
    # Skill
    name = u'威严'
    description = u'当你受到一次伤害后，你可以获得伤害来源的一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MajestyAction:
    def effect_string(act):
        return u'|G【%s】|r脸上挂满黑线，收走了|G【%s】|r的一张牌填补自己的|G威严|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-shikieiki_majesty'


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
    name        = u'四季映姬'
    title       = u'胸不平何以平天下'
    illustrator = u'和茶'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-shikieiki'
    figure_image      = u'thb-figure-shikieiki'
    miss_sound_effect = u'thb-cv-shikieiki_miss'
