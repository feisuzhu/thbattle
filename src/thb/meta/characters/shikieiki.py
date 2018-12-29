# -*- coding: utf-8 -*-
# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import card_desc, ui_meta, passive_clickable
from thb.meta.common import passive_is_action_valid

# -- code --


@ui_meta(characters.shikieiki.Trial)
class Trial:
    # Skill
    name = '审判'
    description = '每当一名角色的判定牌生效前，你可以打出一张牌代替之。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.shikieiki.TrialAction)
class TrialAction:
    def effect_string(self, act):
        return '幻想乡各地巫女妖怪纷纷表示坚决拥护|G【%s】|r将|G【%s】|r的判定结果修改为%s的有关决定！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card)
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-shikieiki_trial1',
            'thb-cv-shikieiki_trial2',
        ])


@ui_meta(characters.shikieiki.Majesty)
class Majesty:
    # Skill
    name = '威严'
    description = '每当你受到一次伤害后，你可以获得伤害来源的一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.shikieiki.MajestyAction)
class MajestyAction:
    def effect_string(self, act):
        return '|G【%s】|r脸上挂满黑线，收走了|G【%s】|r的一张牌填补自己的|G威严|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-shikieiki_majesty'


@ui_meta(characters.shikieiki.TrialHandler)
class TrialHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【审判】吗？'

    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '有罪！')
        else:
            return (False, '请选择一张牌代替当前的判定牌')


@ui_meta(characters.shikieiki.MajestyHandler)
class MajestyHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【威严】吗？'


@ui_meta(characters.shikieiki.Shikieiki)
class Shikieiki:
    # Character
    name        = '四季映姬'
    title       = '胸不平何以平天下'
    illustrator = '和茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-shikieiki'
    figure_image      = 'thb-figure-shikieiki'
    miss_sound_effect = 'thb-cv-shikieiki_miss'
