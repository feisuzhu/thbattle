# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid, my_turn

# -- code --
__metaclass__ = gen_metafunc(characters.remilia)


class SpearTheGungnir:
    # Skill
    name = u'神枪'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SpearTheGungnirAction:
    def effect_string(act):
        return u'|G【%s】|r举起右手，将|G弹幕|r汇聚成一把命运之矛，向|G【%s】|r掷去！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-remilia_stg'


class SpearTheGungnirHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神枪】吗？'


class VampireKiss:
    # Skill
    name = u'红魔之吻'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VampireKissAction:
    def effect_string_before(act):
        return u'|G【%s】|r:“B型血，赞！”' % (
            act.source.ui_meta.char_name
        )

    def sound_effect(act):
        return 'thb-cv-remilia_vampirekiss'


class ScarletMistAttackLimit:
    target_independent = False
    shootdown_message = u'红雾：你只能对距离1的角色使用弹幕'


class ScarletMistAction:
    def effect_string(act):
        src = act.source
        tl = list(act.target_list)
        try:
            tl.remove(src)
        except:
            pass

        return u'|G【%s】|r释放出了|G红雾|r，威严爆表！%s流了鼻血！' % (
            src.ui_meta.char_name,
            u'、'.join([u'|G【%s】|r' % p.ui_meta.char_name for p in tl]),
        )


class ScarletMistEndAction:
    def effect_string(act):
        return u'|G红雾|r结束了。'


class ScarletMist:
    name = u'红雾'

    def clickable(g):
        me = g.me
        return my_turn() and not me.tags['scarlet_mist_used']

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        if skill.associated_cards:
            return (False, u'红雾：请不要选择牌！')

        if not tl:
            return (False, u'红雾：选择目标')

        return (True, u'红雾：选择这些角色获得增益效果')


class Remilia:
    # Character
    char_name = u'蕾米莉亚'
    port_image = 'thb-portrait-remilia'
    figure_image = 'thb-figure-remilia'
    miss_sound_effect = 'thb-cv-remilia_miss'
    description = (
        u'|DB永远幼小的红月 蕾米莉亚 体力：4|r\n'
        u'\n'
        u'|G神枪|r：出现以下情况之一，你可以令你的|G弹幕|r不能被|G擦弹|r抵消：\n'
        u'|B|R>> |r目标角色的体力值 大于 你的体力值。\n'
        u'|B|R>> |r目标角色的手牌数 小于 你的手牌数。\n'
        u'\n'
        u'|G红魔之吻|r：|B锁定技|r，你使用红色|G弹幕|r时无距离限制。当你使用红色|G弹幕|r对一名其他角色造成伤害后，你回复1点体力。\n'
        u'\n'
        u'|G红雾|r：|B协力技|r，|B限定技|r，出牌阶段，你可以选择至多X名其他角色（X为存活道中数量），直到你的下个回合开始阶段，所有角色受到以下影响：\n'
        u'|B|R>> |r你与被选择的角色使用|G弹幕|r时无视距离，且使用|G弹幕|r造成伤害后回复等量的体力。\n'
        u'|B|R>> |r其他角色使用|G弹幕|r时只能指定距离为1的目标。\n'
        u'\n'
        u'|DB（画师：小D@星の妄想乡，CV：VV）|r'
    )
