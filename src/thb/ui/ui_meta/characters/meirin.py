# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, cards, characters
from thb.ui.ui_meta.common import build_handcard, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.meirin)


class RiverBehind:
    # Skill
    name = u'背水'
    description = (
        u'|B觉醒技|r，准备阶段开始时，若你的体力为全场最低时（或之一）且不大于2时，你减少一点体力上限并获得技能|R太极|r。\n'
        u'|B|R>> |b太极|r：你可将|G弹幕|r当|G擦弹|r，|G擦弹|r当|G弹幕|r使用或打出。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Taichi:
    # Skill
    name = u'太极'
    description = u'你可将|G弹幕|r当|G擦弹|r，|G擦弹|r当|G弹幕|r使用或打出。'

    def clickable(game):
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True

            if act.cond([build_handcard(cards.AttackCard)]):
                return True

            if act.cond([build_handcard(cards.GrazeCard)]):
                return True

        except:
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        from thb.cards import AttackCard, GrazeCard
        if len(cl) != 1 or not (cl[0].is_card(AttackCard) or cl[0].is_card(GrazeCard)):
            return (False, u'请选择一张【弹幕】或者【擦弹】！')
        return (True, u'动之则分，静之则合。无过不及，随曲就伸')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        return (
            u'动之则分，静之则合。无过不及，随曲就伸……|G【%s】|r凭|G太极|r之势，轻松应对。'
        ) % (
            source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-meirin_taichi'


class LoongPunch:
    # Skill
    name = u'龙拳'
    description = u'每当你使用|G弹幕|r被|G擦弹|r抵消或使用|G擦弹|r抵消|G弹幕|r时，你可以弃置对方的一张手牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LoongPunchHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【龙拳】吗？'


class LoongPunchAction:
    def effect_string_before(act):
        if act.type == 'attack':
            return u'|G【%s】|r闪过了|G弹幕|r，却没有闪过|G【%s】|r的拳劲，一张手牌被|G【%s】|r震飞！' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
                act.source.ui_meta.name,
            )
        if act.type == 'graze':
            return u'|G【%s】|r擦过弹幕，随即以拳劲沿着弹幕轨迹回震，|G【%s】|r措手不及，一张手牌掉在了地上。' % (
                act.source.ui_meta.name,
                act.target.ui_meta.name,
            )

    def sound_effect(act):
        return 'thb-cv-meirin_loongpunch'


class RiverBehindAwake:
    def effect_string_before(act):
        return u'|G【%s】|r发现自己处境危险，于是强行催动内力护住身体，顺便参悟了太极拳。' % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-meirin_rb'


class Meirin:
    # Character
    name        = u'红美铃'
    title       = u'我只打盹我不翘班'
    illustrator = u'霏茶'
    cv          = u'小羽'

    port_image        = u'thb-portrait-meirin'
    figure_image      = u'thb-figure-meirin'
    miss_sound_effect = ('thb-cv-meirin_miss1', 'thb-cv-meirin_miss2')
