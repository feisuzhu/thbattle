# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn
from thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid

# -- code --


__metaclass__ = gen_metafunc(characters.komachi)


class Komachi:
    # Character
    name        = u'小野塚小町'
    title       = u'乳不巨何以聚人心'
    illustrator = u'渚FUN'
    cv          = u'VV'

    port_image         = u'thb-portrait-komachi'
    figure_image       = u'thb-figure-komachi'
    figure_image_alter = 'thb-figure-komachi_alter'
    miss_sound_effect  = u'thb-cv-komachi_miss'


class Riverside:
    # Skill
    name = u'彼岸'
    description = u'出牌阶段限一次，你可以弃置一张牌并指定一名其他角色，你与其距离视为1直到回合结束，然后若该角色的体力值为全场最少的（或之一），你选择一项：|B|R>> |r摸一张牌，|B|R>> |r弃置其一张牌。'

    def clickable(g):
        if not my_turn(): return False
        if limit1_skill_used('riverside_tag'): return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def is_action_valid(g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, u'请选择一张牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards', 'equips'):
            return (False, u'WTF?!')

        if card.is_card(cards.Skill):
            return (False, u'你不可以像这样组合技能')

        return (True, u'近一点~再近一点~~')

    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r使用了|G彼岸|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name
        )

    def sound_effect(act):
        return 'thb-cv-komachi_riverside'


class RiversideAction:
    # choose_option meta
    choose_option_buttons = ((u'弃置一张牌', 'drop'), (u'摸一张牌', 'draw'))
    choose_option_prompt = u'彼岸：你希望发动的效果？'


class ReturningAwake:
    def effect_string(act):
        return u'|G【%s】|r：“啊啊不能再偷懒啦！要被四季大人说教啦！”' % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-komachi_awake'


class Returning:
    # Skill
    name = u'归航'
    description = (
        u'|B觉醒技|r，准备阶段开始时，若你体力值小于手牌数且不大于2，你减1点体力上限并获得技能|R渡钱|r\n'
        u'|B|R>> |b渡钱|r：每当你对距离1的其他角色造成伤害后，你可以获得其一张牌。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FerryFee:
    # Skill
    name = u'渡钱'
    description = u'每当你对距离1的其他角色造成伤害后，你可以获得其一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FerryFeeEffect:
    def effect_string(act):
        return u'|G【%s】|r收走了|G【%s】|r的一张牌作为|G渡钱|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-komachi_ferryfee'


class FerryFeeHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动渡钱吗？'
