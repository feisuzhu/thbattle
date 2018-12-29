# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Skill
from thb.meta.common import limit1_skill_used, my_turn, passive_clickable, passive_is_action_valid
from thb.meta.common import ui_meta


# -- code --


@ui_meta(characters.komachi.Komachi)
class Komachi:
    # Character
    name        = '小野塚小町'
    title       = '乳不巨何以聚人心'
    illustrator = '渚FUN'
    cv          = 'VV'

    port_image        = 'thb-portrait-komachi'
    figure_image      = 'thb-figure-komachi'
    miss_sound_effect = 'thb-cv-komachi_miss'


@ui_meta(characters.komachi.Riverside)
class Riverside:
    # Skill
    name = '彼岸'
    description = '出牌阶段限一次，你可以弃置一张牌并指定一名其他角色，你与其距离视为1直到回合结束，然后若该角色的体力值为全场最少的（或之一），你选择一项：|B|R>> |r摸一张牌，|B|R>> |r弃置其一张牌。'

    def clickable(self, g):
        if not my_turn(): return False
        if limit1_skill_used('riverside_tag'): return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def is_action_valid(self, g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, '请选择一张牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards', 'equips'):
            return (False, 'WTF?!')

        if card.is_card(Skill):
            return (False, '你不可以像这样组合技能')

        return (True, '近一点~再近一点~~')

    def effect_string(self, act):
        return '|G【%s】|r对|G【%s】|r使用了|G彼岸|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name
        )

    def sound_effect(self, act):
        return 'thb-cv-komachi_riverside'


@ui_meta(characters.komachi.RiversideAction)
class RiversideAction:
    # choose_option meta
    choose_option_buttons = (('弃置一张牌', 'drop'), ('摸一张牌', 'draw'))
    choose_option_prompt = '彼岸：你希望发动的效果？'


@ui_meta(characters.komachi.ReturningAwake)
class ReturningAwake:
    def effect_string(self, act):
        return '|G【%s】|r：“啊啊不能再偷懒啦！要被四季大人说教啦！”' % (
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-komachi_awake'


@ui_meta(characters.komachi.Returning)
class Returning:
    # Skill
    name = '归航'
    description = (
        '|B觉醒技|r，准备阶段开始时，若你体力值小于手牌数且不大于2，你减1点体力上限并获得技能|R渡钱|r\n'
        '|B|R>> |b渡钱|r：每当你对距离1的其他角色造成伤害后，你可以获得其一张牌。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.komachi.FerryFee)
class FerryFee:
    # Skill
    name = '渡钱'
    description = '每当你对距离1的其他角色造成伤害后，你可以获得其一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.komachi.FerryFeeEffect)
class FerryFeeEffect:
    def effect_string(self, act):
        return '|G【%s】|r收走了|G【%s】|r的一张牌作为|G渡钱|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-komachi_ferryfee'


@ui_meta(characters.komachi.FerryFeeHandler)
class FerryFeeHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动渡钱吗？'
