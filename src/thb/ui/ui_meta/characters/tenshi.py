# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.tenshi)


class Masochist:
    # Skill
    name = u'抖Ｍ'
    description = u'每当你受到1点伤害后，你可以观看牌堆顶的两张牌，并将这些牌交给至少一名角色。'

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
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-tenshi_masochist'


class ScarletPerception:
    # Skill
    name = u'绯想'
    description = u'|B锁定技|r，距离1以内的角色的红色判定牌置入弃牌堆时，你获得之。'

    # 此处OL结算有bug，当红色判定被改判成另一张红色时，应该可以发动2次|G绯想|r，并获得2张红色判定牌。
    # 参考曹植相关FAQ:
    # [Q]其他角色进行判定结算时，判定牌为梅花，司马懿发动|G鬼才|r打出梅花牌代替，在此过程中曹植可以发动几次|G落英|r？
    # [A]两次。第一张判定牌被替代后进入弃牌堆时曹植可以发动第一次|G落英|r，第二张判定牌虽然是司马懿以打出的方式发动|G鬼才|r，但是该牌打出后是成为了判定牌才进入弃牌堆，并非打出后直接进入弃牌堆，因此曹植可以发动第二次|G落英|r。

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ScarletPerceptionAction:
    def effect_string(act):
        return u'|G【%s】|r获得了%s' % (
            act.source.ui_meta.name,
            card_desc(act.card)
        )

    def sound_effect(act):
        return 'thb-cv-tenshi_sp'


class Tenshi:
    # Character
    name        = u'比那名居天子'
    title       = u'有顶天的大M子'
    illustrator = u'月见'
    cv          = u'VV'

    port_image        = u'thb-portrait-tenshi'
    figure_image      = u'thb-figure-tenshi'
    miss_sound_effect = u'thb-cv-tenshi_miss'
