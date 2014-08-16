# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.flandre)


class Flandre:
    # Character
    char_name = u'芙兰朵露'
    port_image = gres.flandre_port
    description = (
        u'|DB玩坏你哦 芙兰朵露 体力：4|r\n\n'
        u'|G破坏冲动|r：|B锁定技|r，回合结束阶段开始时，若你本回合内没有造成过伤害，你失去一点体力并对距离1以内的一名角色造成一点伤害。\n\n'
        u'|G四重存在|r：当你受到一次伤害时，你可以减少一点体力上限来防止该伤害。|B锁定技|r，当你的体力上限为1时，你造成的伤害+1。'
    )


class DestructionImpulse:
    # Skill
    name = u'破坏冲动'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DestructionImpulseHandler:
    def choose_card_text(g, act, cards):
        if cards:
            return (False, u'请不要选择牌！')

        return (True, u'玩坏你哦')

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'请选择1名距离1以内的玩家，对其造成一点伤害')

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
