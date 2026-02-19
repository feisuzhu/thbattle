# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N

# -- code --


@ui_meta(characters.mokou.Mokou)
class Mokou:
    # Character
    name        = '藤原妹红'
    title       = 'FFF团资深团员'
    illustrator = '六仔OwO'
    cv          = '小羽'

    port_image        = 'thb-portrait-mokou'
    figure_image      = 'thb-figure-mokou'
    miss_sound_effect = 'thb-cv-mokou_miss'


@ui_meta(characters.mokou.Ashes)
class Ashes:
    # Skill
    name = '浴火'
    description = '结束阶段开始时，你可以流失1点体力，然后摸两张牌。'


@ui_meta(characters.mokou.AshesAction)
class AshesAction:
    def effect_string_before(self, act):
        return f'{N.char(act.target)}：“不~可~饶~恕~！”'

    def sound_effect(self, act):
        return 'thb-cv-mokou_ashes'


@ui_meta(characters.mokou.AshesHandler)
class AshesHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>浴火</style>吗？'


@ui_meta(characters.mokou.Reborn)
class Reborn:
    # Skill
    name = '重生'
    description = '准备阶段开始时，你可以弃置X张红色牌，然后回复1点体力。（X为你的体力）'


@ui_meta(characters.mokou.RebornAction)
class RebornAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}使用了<style=Skill.Name>重生</style>。'

    def sound_effect(self, act):
        return 'thb-cv-mokou_reborn'


@ui_meta(characters.mokou.RebornHandler)
class RebornHandler:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '弃置这些牌并回复1点体力')
        else:
            return (False, f'<style=Skill.Name>重生</style>：选择{act.target.life}张红色牌弃置并回复一点体力')
