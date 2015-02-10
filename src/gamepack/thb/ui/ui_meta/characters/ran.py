# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.ran)


class Prophet:
    # Skill
    name = u'神算'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExtremeIntelligence:
    # Skill
    name = u'极智'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ProphetHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神算】吗？'


class ProphetAction:
    def effect_string_before(act):
        return u'众人正准备接招呢，|G【%s】|r却掐着指头算了起来…' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-ran_prophet'


class ExtremeIntelligenceAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'再来！')
        else:
            return (False, u'弃置1张牌并发动【极智】')

    def effect_string_before(act):
        return (
            u'|G【%s】|r刚松了一口气，却看见一张一模一样的符卡从|G【%s】|r的方向飞来！'
        ) % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-ran_ei'


class NakedFox:
    # Skill
    name = u'素裸'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class NakedFoxAction:
    def effect_string_before(act):
        if act.dmgamount <= 1:
            s = u'符卡飞到了|G【%s】|r毛茸茸的大尾巴里，然后……就没有然后了……'
        else:
            s = u'符卡飞到了|G【%s】|r毛茸茸的大尾巴里，恩……似乎还是有点疼……'

        return s % act.target.ui_meta.char_name


class Ran:
    # Character
    char_name = u'八云蓝'
    port_image = 'thb-portrait-ran'
    miss_sound_effect = 'thb-cv-ran_miss'
    description = (
        u'|DB天河一号的核心 八云蓝 体力：3|r\n\n'
        u'|G神算|r：准备阶段开始时，你可以观看牌堆顶的X张牌，将其中任意数量的牌以任意顺序的置于牌堆顶，其余以任意顺序置于牌堆底。（X为场上存活角色的数量，且至多为5）\n\n'
        u'|G极智|r：你的回合外，当有非延时符卡的效果对一名角色生效后，你可以弃置一张牌使该效果对该角色重新进行一次结算，此时效果来源视为你。每轮限一次。\n\n'
        u'|G素裸|r：|B锁定技|r，当你没有手牌时，你受到的符卡伤害-1。\n\n'
        u'|DB（画师：Pixiv ID 27367823，CV：shourei小N）|r'
    )
