# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.cards.classes import AttackCard, GrazeCard
from thb.meta.common import build_handcard, passive_clickable, passive_is_action_valid, ui_meta


# -- code --


@ui_meta(characters.meirin.RiverBehind)
class RiverBehind:
    # Skill
    name = '背水'
    description = (
        '|B觉醒技|r，准备阶段开始时，若你体力值为全场最低或之一且不大于2时，你减1点体力上限并获得技能|R太极|r。\n'
        '|B|R>> |b太极|r：你可将|G弹幕|r当|G擦弹|r，|G擦弹|r当|G弹幕|r使用或打出。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.meirin.Taichi)
class Taichi:
    # Skill
    name = '太极'
    description = '你可将|G弹幕|r当|G擦弹|r，|G擦弹|r当|G弹幕|r使用或打出。'

    def clickable(self, g):
        try:
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True

            if act.cond([build_handcard(AttackCard)]):
                return True

            if act.cond([build_handcard(GrazeCard)]):
                return True

        except Exception:
            pass

        return False

    def is_complete(self, g, skill):
        cl = skill.associated_cards
        from thb.cards.classes import AttackCard, GrazeCard
        if len(cl) != 1 or not (cl[0].is_card(AttackCard) or cl[0].is_card(GrazeCard)):
            return (False, '请选择一张【弹幕】或者【擦弹】！')
        return (True, '动之则分，静之则合。无过不及，随曲就伸')

    def is_action_valid(self, g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        return (
            '动之则分，静之则合。无过不及，随曲就伸……|G【%s】|r凭|G太极|r之势，轻松应对。'
        ) % (
            source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-meirin_taichi'


@ui_meta(characters.meirin.LoongPunch)
class LoongPunch:
    # Skill
    name = '龙拳'
    description = '每当你使用的|G弹幕|r被其他角色使用的|G擦弹|r抵消时，或其他角色使用的|G弹幕|r被你使用的|G擦弹|r抵消时，你可以弃置其1张手牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.meirin.LoongPunchHandler)
class LoongPunchHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【龙拳】吗？'


@ui_meta(characters.meirin.LoongPunchAction)
class LoongPunchAction:
    def effect_string_before(self, act):
        if act.type == 'attack':
            return '|G【%s】|r闪过了|G弹幕|r，却没有闪过|G【%s】|r的拳劲，一张手牌被|G【%s】|r震飞！' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
                act.source.ui_meta.name,
            )
        if act.type == 'graze':
            return '|G【%s】|r擦过弹幕，随即以拳劲沿着弹幕轨迹回震，|G【%s】|r措手不及，一张手牌掉在了地上。' % (
                act.source.ui_meta.name,
                act.target.ui_meta.name,
            )

    def sound_effect(self, act):
        return 'thb-cv-meirin_loongpunch'


@ui_meta(characters.meirin.RiverBehindAwake)
class RiverBehindAwake:
    def effect_string_before(self, act):
        return '|G【%s】|r发现自己处境危险，于是强行催动内力护住身体，顺便参悟了太极拳。' % (
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-meirin_rb'


@ui_meta(characters.meirin.Meirin)
class Meirin:
    # Character
    name        = '红美铃'
    title       = '我只打盹我不翘班'
    illustrator = '霏茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-meirin'
    figure_image      = 'thb-figure-meirin'
    miss_sound_effect = ('thb-cv-meirin_miss1', 'thb-cv-meirin_miss2')
