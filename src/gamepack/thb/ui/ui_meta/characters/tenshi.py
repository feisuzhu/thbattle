# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, card_desc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.tenshi)


class Masochist:
    # Skill
    name = u'抖Ｍ'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MasochistHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【抖Ｍ】吗？'


class MasochistAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'给你牌~')
        else:
            return (False, u'请选择你要给出的牌（否则给自己）')

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'给你牌~')

    def effect_string_before(act):
        return u'不过|G【%s】|r好像很享受的样子…' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return gres.cv.tenshi_masochist


class ScarletPerception:
    # Skill
    name = u'绯想'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ScarletPerceptionAction:
    def effect_string(act):
        return u'|G【%s】|r获得了%s' % (
            act.source.ui_meta.char_name,
            card_desc(act.card)
        )

    def sound_effect(act):
        return gres.cv.tenshi_sp


class Tenshi:
    # Character
    char_name = u'比那名居天子'
    port_image = gres.tenshi_port
    miss_sound_effect = gres.cv.tenshi_miss
    description = (
        u'|DB有顶天的大M子 比那名居天子 体力：3|r\n\n'
        u'|G抖Ｍ|r：每当你受到X点伤害，你可以摸X*2张牌，然后将这些牌分配给任意的角色。\n\n'
        u'|G绯想|r：与你距离为1以内的角色的红色判定牌进入弃牌堆后，你获得之。\n\n'
        u'|DB（画师：Danbooru post 482239，CV：VV）|r'
    )
