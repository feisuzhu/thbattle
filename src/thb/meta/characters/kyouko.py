# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import VirtualCard
from thb.meta.common import ui_meta, N


# -- code --


@ui_meta(characters.kyouko.Kyouko)
class Kyouko:
    # Character
    name        = '幽谷响子'
    title       = '诵经的山彦'
    illustrator = '月见'
    designer    = '蝶之羽风暂留此'
    cv          = '小羽'

    port_image        = 'thb-portrait-kyouko'
    figure_image      = 'thb-figure-kyouko'
    miss_sound_effect = 'thb-cv-kyouko_miss'


@ui_meta(characters.kyouko.Echo)
class Echo:
    # Skill
    name = '回响'
    description = '每当你受到一次伤害后，你可以获得对你造成伤害的牌，若此牌为<style=Card.Name>弹幕</style>，你可以改为令一名其他角色获得之。'


@ui_meta(characters.kyouko.Resonance)
class Resonance:
    # Skill
    name = '共振'
    description = '当你对其他角色使用的<style=Card.Name>弹幕</style>结算完毕后，你可以指定另一名其他角色，被指定角色可以对其使用一张无视距离的<style=Card.Name>弹幕</style>。'


@ui_meta(characters.kyouko.EchoHandler)
class EchoHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('放弃', False))
    choose_option_prompt = '是否发动<style=Skill.Name>回响</style>'

    # choose_players
    def target(self, pl):
        if not pl:
            return (False, '<style=Skill.Name>回响</style>：请选择获得<style=Card.Name>弹幕</style>的角色')

        return (True, '回响···')


@ui_meta(characters.kyouko.ResonanceAction)
class ResonanceAction:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, f'<style=Card.Name>共振</style>：对{N.char(act.victim)}使用弹幕')
        else:
            return (False, f'<style=Card.Name>共振</style>：请选择一张弹幕对{N.char(act.victim)}使用')

    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}发动了<style=Skill.Name>共振</style>。'

    def ray(self, act):
        src, tgt = act.source, act.target
        return [(src, tgt)]

    def sound_effect(self, act):
        return 'thb-cv-kyouko_resonance'


@ui_meta(characters.kyouko.EchoAction)
class EchoAction:

    def effect_string_before(self, act):
        c = VirtualCard.unwrap([act.card])
        return f'{N.char(act.source)}发动了<style=Skill.Name>回响</style>，{N.char(act.target)}获得了{N.card(c)}。'

    def sound_effect(self, act):
        return 'thb-cv-kyouko_echo'


@ui_meta(characters.kyouko.ResonanceHandler)
class ResonanceHandler:
    # choose_players
    def target(self, pl):
        if not pl:
            return (False, '<style=Skill.Name>共振</style>：请选择一名角色使用<style=Skill.Name>弹幕</style>')

        return (True, '发动<style=Skill.Name>共振</style>')
