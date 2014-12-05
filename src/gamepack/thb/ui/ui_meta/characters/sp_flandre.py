# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.sp_flandre)


class SpFlandre:
    # Character
    char_name = u'SP芙兰朵露'
    port_image = 'thb-portrait-sp_flandre'
    figure_image = 'thb-figure-sp_flandre'
    miss_sound_effect = 'thb-cv-spflandre_miss'
    description = (
        u'|DB玩坏你哦 SP芙兰朵露 体力：4|r\n\n'
        u'|G破坏冲动|r：|B锁定技|r，结束阶段开始时，若你本回合内没有造成过伤害，你失去1点体力并对最近的一名其他角色造成1点伤害。\n\n'
        u'|G四重存在|r：当你受到一次伤害时，你可以减少1点体力上限来防止该伤害。|B锁定技|r，当你的体力为1时，你造成的伤害+1。\n\n'
        u'|DB（画师：Vivicat from 幻想梦斗符，CV：shourei小N）|r'
    )


class DestructionImpulse:
    # Skill
    name = u'破坏冲动'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DestructionImpulseAction:
    def effect_string_before(act):
        return u'|G【%s】|r：“|G【%s】|r来陪我玩好不好？”' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-spflandre_destructionimpulse'


class DestructionImpulseHandler:
    def choose_card_text(g, act, cards):
        if cards:
            return (False, u'请不要选择牌！')

        return (True, u'玩坏你哦')

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'请选择1名距离最近的玩家，对其造成一点伤害')

        return (True, u'玩坏你哦')


class FourOfAKind:
    # Skill
    name = u'四重存在'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FourOfAKindHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【四重存在】吗？'


class FourOfAKindAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G四重存在|r，防止了此次伤害。' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-spflandre_fourofakind'
