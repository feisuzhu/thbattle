# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, my_turn, passive_clickable
from thb.meta.common import passive_is_action_valid


# -- code --


@ui_meta(characters.ran.Prophet)
class Prophet:
    # Skill
    name = '神算'
    description = '准备阶段开始时，你可以观看牌堆顶的X张牌，将其中任意数量的牌以任意顺序置于牌堆顶，其余以任意顺序置于牌堆底。（X为存活角色数且至多为5）'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.ran.ExtremeIntelligence)
class ExtremeIntelligence:
    # Skill
    name = '极智'
    description = '每轮限一次，你的回合外，当非延时符卡对一名角色生效后，你可以弃置一张牌，令该符卡效果对那名角色重新进行一次结算，此时使用者视为你。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.ran.ExtremeIntelligenceKOF)
class ExtremeIntelligenceKOF:
    # Skill
    name = '极智'
    description = '出牌阶段限一次，你可以将一张手牌当你本回合上一张使用过的非延时符卡使用。'

    def clickable(self, game):
        me = game.me

        if not (my_turn() and (me.cards or me.showncards)):
            return False

        if ttags(me)['ran_eikof_tag']:
            return False

        if not ttags(me)['ran_eikof_card']:
            return False

        return True

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.ran.ExtremeIntelligenceKOF)

        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张牌！')

        if cl[0].resides_in not in (g.me.cards, g.me.showncards):
            return (False, '请选择手牌！')

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        src, tl, card = act.source, act.target_list, act.card
        s = '|G【%s】|r发动了|G极智|r技能，将|G%s|r当作|G%s|r对%s使用。' % (
            src.ui_meta.name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            '、'.join(["|G【%s】|r" % i.ui_meta.name for i in tl]),
        )
        return s


@ui_meta(characters.ran.ProphetHandler)
class ProphetHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【神算】吗？'


@ui_meta(characters.ran.ProphetAction)
class ProphetAction:
    def effect_string_before(self, act):
        return '众人正准备接招呢，|G【%s】|r却掐着指头算了起来…' % (
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-ran_prophet'


@ui_meta(characters.ran.ExtremeIntelligenceAction)
class ExtremeIntelligenceAction:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '再来！')
        else:
            return (False, '弃置1张牌并发动【极智】')

    def effect_string_before(self, act):
        return (
            '|G【%s】|r刚松了一口气，却看见一张一模一样的符卡从|G【%s】|r的方向飞来！'
        ) % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-ran_ei'


@ui_meta(characters.ran.NakedFox)
class NakedFox:
    # Skill
    name = '素裸'
    description = '|B锁定技|r，若你没有手牌，符卡对你造成的伤害-1。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.ran.NakedFoxAction)
class NakedFoxAction:
    def effect_string_before(self, act):
        if act.dmgamount <= 1:
            s = '符卡飞到了|G【%s】|r毛茸茸的大尾巴里，然后……就没有然后了……'
        else:
            s = '符卡飞到了|G【%s】|r毛茸茸的大尾巴里，恩……似乎还是有点疼……'

        return s % act.target.ui_meta.name


@ui_meta(characters.ran.Ran)
class Ran:
    # Character
    name        = '八云蓝'
    title       = '天河一号的核心'
    illustrator = '霏茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-ran'
    figure_image      = 'thb-figure-ran'
    miss_sound_effect = 'thb-cv-ran_miss'


@ui_meta(characters.ran.RanKOF)
class RanKOF:
    # Character
    name        = '八云蓝'
    title       = '天河一号的核心'
    illustrator = '霏茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-ran'
    figure_image      = 'thb-figure-ran'
    miss_sound_effect = 'thb-cv-ran_miss'

    notes = '|RKOF修正角色|r'
