# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_is_action_valid, passive_clickable

# -- code --

__metaclass__ = gen_metafunc(characters.reisen)


class Reisen:
    # Character
    char_name = u'铃仙'
    port_image = 'thb-portrait-reisen'
    figure_image = 'thb-figure-reisen'
    miss_sound_effect = 'thb-cv-reisen_miss'
    description = (
        u'|DB永琳的首席药品品尝官 铃仙·优昙华院·因幡 体力：4|r\n\n'
        u'|G狂气|r：你因为|G弹幕|r或|G弹幕战|r对一名其他角色造成伤害后，你可以令其获得技能|G丧心|r。\n\n'
        u'|G生药|r：你因为|G麻薯|r而回复体力后，你可以获得喝醉状态。\n\n'
        u'|R丧心|r：|B锁定技|r，出牌阶段，你不能使用除|G弹幕|r以外的卡牌。你使用|G弹幕|r只能指定距离最近的目标。结束阶段开始时，你失去此技能。\n\n'
        u'|DB（画师：镜_Area@幻想梦斗符，CV：小羽）|r'
    )


class Lunatic:
    # Skill
    name = u'狂气'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Discarder:
    # Skill
    name = u'丧心'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MahjongDrug:
    # Skill
    name = u'生药'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MahjongDrugAction:
    def effect_string(act):
        return u'|G【%s】|r：“国士无双之药，认准蓝瓶的！”' % act.target.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-reisen_mahjongdrug'


class MahjongDrugHandler:
    choose_option_prompt = u'你要发动【生药】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class LunaticHandler:
    choose_option_prompt = u'你要发动【狂气】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class LunaticAction:
    def effect_string(act):
        return u'|G【%s】|r：“给你们看看全部的，月的疯狂！”' % act.source.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-reisen_lunatic'


class DiscarderAttackOnly:
    shootdown_message = u'【丧心】你不能使用弹幕以外的牌。'


class DiscarderDistanceLimit:
    shootdown_message = u'【丧心】你只能对离你最近的角色使用弹幕。'
