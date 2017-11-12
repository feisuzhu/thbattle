# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.sp_flandre)


class SpFlandre:
    # Character
    name        = u'SP芙兰朵露'
    title       = u'玩坏你哦'
    illustrator = u'Vivicat@幻想梦斗符'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-sp_flandre'
    figure_image      = u'thb-figure-sp_flandre'
    miss_sound_effect = u'thb-cv-spflandre_miss'


class DestructionImpulse:
    # Skill
    name = u'破坏冲动'
    description = u'|B锁定技|r，结束阶段开始时，若你本回合没有造成过伤害，你失去1点体力并对距离最近的一名其他角色造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DestructionImpulseAction:
    def effect_string_before(act):
        return u'|G【%s】|r：“|G【%s】|r来陪我玩好不好？”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
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
    description = u'每当你受到一次不大于你当前体力值的伤害时，你可以减少1点体力上限并防止此伤害；你体力值为1时，你为伤害来源的卡牌造成的伤害+1。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FourOfAKindHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【四重存在】吗？'


class FourOfAKindAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G四重存在|r，防止了此次伤害。' % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-spflandre_fourofakind'
