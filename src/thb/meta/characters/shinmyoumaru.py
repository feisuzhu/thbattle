# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.shinmyoumaru.MiracleMallet)
class MiracleMallet:
    # Skill
    name = '万宝槌'
    description = '当一名角色的判定牌生效前，你可以用一张点数大于此牌的牌替换之。'


@ui_meta(characters.shinmyoumaru.MiracleMalletAction)
class MiracleMalletAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}将{N.char(act.target)}的判定结果改为{N.card(act.card)}。'

    def sound_effect(self, act):
        return random.choice((
            'thb-cv-shinmyoumaru_mallet1',
            'thb-cv-shinmyoumaru_mallet2',
        ))


@ui_meta(characters.shinmyoumaru.VengeOfTsukumogami)
class VengeOfTsukumogami:
    # Skill
    name = '付丧神之怨'
    description = '每当其他角色装备区的牌因弃置而置入弃牌堆时，你可以进行一次判定，若为9~K，你对其造成1点伤害。'


@ui_meta(characters.shinmyoumaru.VengeOfTsukumogamiAction)
class VengeOfTsukumogamiAction:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}发动了<style=Skill.Name>付丧神之怨</style>。'

    def sound_effect(self, act):
        return random.choice((
            'thb-cv-shinmyoumaru_venge1',
            'thb-cv-shinmyoumaru_venge2',
        ))


@ui_meta(characters.shinmyoumaru.MiracleMalletHandler)
class MiracleMalletHandler:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '发动<style=Skill.Name>万宝槌</style>！')
        else:
            return (False, '请选择一张牌点数更大的牌代替当前的判定牌')


@ui_meta(characters.shinmyoumaru.VengeOfTsukumogamiHandler)
class VengeOfTsukumogamiHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(self, act):
        return f'你要发动<style=Skill.Name>付丧神之怨</style>吗（对{N.char(act.target)}）？'


@ui_meta(characters.shinmyoumaru.Shinmyoumaru)
class Shinmyoumaru:
    # Character
    name        = '少名针妙丸'
    title       = '进击的小人'
    illustrator = '六仔OwO'
    designer    = 'yourccz95'
    cv          = '小羽'

    port_image        = 'thb-portrait-shinmyoumaru'
    figure_image      = 'thb-figure-shinmyoumaru'
    miss_sound_effect = 'thb-cv-shinmyoumaru_miss'
