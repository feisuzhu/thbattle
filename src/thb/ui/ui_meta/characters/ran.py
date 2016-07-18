# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.ran)


class Prophet:
    # Skill
    name = u'神算'
    description = u'准备阶段开始时，你可以观看牌堆顶的X张牌，将其中任意数量的牌以任意顺序的置于牌堆顶，其余以任意顺序置于牌堆底。（X为场上存活角色的数量，且至多为5）'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExtremeIntelligence:
    # Skill
    name = u'极智'
    description = u'你的回合外，当有非延时符卡的效果对一名角色生效后，你可以弃置一张牌使该效果对该角色重新进行一次结算，此时效果来源视为你。每轮限一次。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExtremeIntelligenceKOF:
    # Skill
    name = u'极智'
    description = u'出牌阶段限一次，你可以将一张手牌当你本回合上一张使用过的非延时符卡使用。'

    def clickable(game):
        me = game.me

        if not (my_turn() and (me.cards or me.showncards)):
            return False

        if ttags(me)['ran_eikof_tag']:
            return False

        if not ttags(me)['ran_eikof_card']:
            return False

        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.ran.ExtremeIntelligenceKOF)

        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')

        if cl[0].resides_in not in (g.me.cards, g.me.showncards):
            return (False, u'请选择手牌！')

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        src, tl, card = act.source, act.target_list, act.card
        s = u'|G【%s】|r发动了|G极智|r技能，将|G%s|r当作|G%s|r对%s使用。' % (
            src.ui_meta.name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            u'、'.join([u"|G【%s】|r" % i.ui_meta.name for i in tl]),
        )
        return s


class ProphetHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神算】吗？'


class ProphetAction:
    def effect_string_before(act):
        return u'众人正准备接招呢，|G【%s】|r却掐着指头算了起来…' % (
            act.target.ui_meta.name,
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
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-ran_ei'


class NakedFox:
    # Skill
    name = u'素裸'
    description = u'|B锁定技|r，当你没有手牌时，你受到的符卡伤害-1。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class NakedFoxAction:
    def effect_string_before(act):
        if act.dmgamount <= 1:
            s = u'符卡飞到了|G【%s】|r毛茸茸的大尾巴里，然后……就没有然后了……'
        else:
            s = u'符卡飞到了|G【%s】|r毛茸茸的大尾巴里，恩……似乎还是有点疼……'

        return s % act.target.ui_meta.name


class Ran:
    # Character
    name        = u'八云蓝'
    title       = u'天河一号的核心'
    illustrator = u'霏茶'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-ran'
    figure_image      = u'thb-figure-ran'
    miss_sound_effect = u'thb-cv-ran_miss'


class RanKOF:
    # Character
    name        = u'八云蓝'
    title       = u'天河一号的核心'
    illustrator = u'霏茶'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-ran'
    figure_image      = u'thb-figure-ran'
    miss_sound_effect = u'thb-cv-ran_miss'

    notes = u'|RKOF修正角色|r'
