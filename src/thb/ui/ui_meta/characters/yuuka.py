# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import build_handcard, gen_metafunc, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.yuuka)


class ReversedScales:
    # Skill
    name = u'逆鳞'
    description = u'每当你成为其他角色使用的单体符卡的目标时，你可以将其视为|G弹幕战|r；你的回合外，你可以将一张手牌当做|G弹幕|r使用或打出。'

    def clickable(game):
        me = game.me
        if my_turn():
            return False

        if not (me.cards or me.showncards):
            return False

        try:
            act = game.action_stack[-1]
            return act.cond([build_handcard(cards.AttackCard)])
        except:
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择1张牌！')

        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r用和善的眼神看了|G【%s】|r一眼。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-yuuka_flowerqueen'


class Sadist:
    # Skill
    name = u'施虐'
    description = u'当你击坠一名角色时，你可以对攻击范围内一名其他角色造成1点伤害；你对残机数为1的其他角色造成的伤害+1。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SadistKOF:
    # Skill
    name = u'施虐'
    description = u'|B锁定技|r，当你击坠对手后，你摸2张牌并对其下一名登场角色造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ReversedScalesAction:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r：“来正面上我啊！”'
        ) % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-yuuka_rs'


class SadistAction:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r又看了看|G【%s】|r：“你也要尝试一下么！”'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-yuuka_sadist'


class SadistKOFDamageAction:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r又看了看|G【%s】|r：“你也要尝试一下么！”'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-yuuka_sadist'


class SadistHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'发动【施虐】')
        else:
            return (False, u'【施虐】：请弃置一张牌')

    def target(pl):
        if not pl:
            return (False, u'【施虐】：请选择1名玩家')

        return (True, u'发动【施虐】')


class ReversedScalesHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【逆鳞】吗？'


class Yuuka:
    # Character
    name        = u'风见幽香'
    title       = u'四季的鲜花之主'
    illustrator = u'霏茶'
    cv          = u'VV'

    port_image        = u'thb-portrait-yuuka'
    figure_image      = u'thb-figure-yuuka'
    miss_sound_effect = u'thb-cv-yuuka_miss'


class YuukaKOF:
    # Character
    name        = u'风见幽香'
    title       = u'四季的鲜花之主'
    illustrator = u'霏茶'
    cv          = u'VV'

    port_image        = u'thb-portrait-yuuka'
    figure_image      = u'thb-figure-yuuka'
    miss_sound_effect = u'thb-cv-yuuka_miss'

    notes = u'|RKOF修正角色'
