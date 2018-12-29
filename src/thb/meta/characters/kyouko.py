# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import VirtualCard
from thb.meta.common import card_desc, passive_clickable, passive_is_action_valid, ui_meta


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
    description = '每当你受到一次伤害后，你可以获得对你造成伤害的牌，若此牌为|G弹幕|r，你可以改为令一名其他角色获得之。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.kyouko.Resonance)
class Resonance:
    # Skill
    name = '共振'
    description = '当你对其他角色使用的|G弹幕|r结算完毕后，你可以指定另一名其他角色，该角色可以对其使用一张无视距离的|G弹幕|r。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.kyouko.EchoHandler)
class EchoHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('放弃', False))
    choose_option_prompt = '是否发动【回响】'

    # choose_players
    def target(self, pl):
        if not pl:
            return (False, '回响：请选择获得【弹幕】的角色')

        return (True, '回响···')


@ui_meta(characters.kyouko.ResonanceAction)
class ResonanceAction:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '共振：对%s使用弹幕' % act.target.ui_meta.name)
        else:
            return (False, '共振：请选择一张弹幕对%s使用' % act.target.ui_meta.name)

    def effect_string_before(self, act):
        return '|G【%s】|r对|G【%s】|r发动了|G共振|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def ray(self, act):
        src, tgt = act.source, act.target
        return [(src, tgt)]

    def sound_effect(self, act):
        return 'thb-cv-kyouko_resonance'


@ui_meta(characters.kyouko.EchoAction)
class EchoAction:

    def effect_string_before(self, act):
        return '|G【%s】|r发动了|G回响|r，|G【%s】|r获得了%s' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(VirtualCard.unwrap([act.card])),
        )

    def sound_effect(self, act):
        return 'thb-cv-kyouko_echo'


@ui_meta(characters.kyouko.ResonanceHandler)
class ResonanceHandler:
    # choose_players
    def target(self, pl):
        if not pl:
            return (False, '共振：请选择一名角色使用【弹幕】')

        return (True, '发动【共振】')
