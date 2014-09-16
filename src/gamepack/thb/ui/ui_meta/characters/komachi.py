# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres


__metaclass__ = gen_metafunc(characters.komachi)


class Komachi:
    # Character
    char_name = u'小野塚小町'
    port_image = gres.komachi_port
    figure_image = gres.komachi_figure
    figure_image_alter = gres.komachi_figure_alter
    miss_sound_effect = gres.cv.komachi_miss
    description = (
        u'|DB乳不巨何以聚人心 小野塚小町 体力：4|r\n\n'
        u'|G彼岸|r：出牌阶段，你可以弃置一张牌并指定一名角色，你与其距离视为1直到回合结束。若该角色为全场体力最少的角色（或之一），你可以弃置其一张牌或摸一张牌。每阶段限一次。\n\n'
        u'|G归航|r：|B觉醒技|r，回合开始阶段，若你的体力值低于手牌数且小于等于2，你失去一点体力上限并获得技能|R渡钱|r。\n\n'
        u'|R渡钱|r：你对距离为1的角色造成一次伤害后，你可以获得其一张牌。\n\n'
        u'|DB（画师：渚FUN，CV：VV）|r'
    )


class Riverside:
    # Skill
    name = u'彼岸'

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
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def sound_effect(act):
        return gres.cv.komachi_riverside


class RiversideAction:
    # choose_option meta
    choose_option_buttons = ((u'弃置一张牌', 'drop'), (u'摸一张牌', 'draw'))
    choose_option_prompt = u'彼岸：你希望发动的效果？'


class ReturningAwake:
    def effect_string(act):
        return u'|G【%s】|r：“啊啊不能再偷懒啦！要被四季大人说教啦！”' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return gres.cv.komachi_awake


class Returning:
    # Skill
    name = u'归航'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FerryFee:
    # Skill
    name = u'渡钱'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FerryFeeEffect:
    def effect_string(act):
        return u'|G【%s】|r收走了|G【%s】|r的一张牌作为|G渡钱|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return gres.cv.komachi_ferryfee


class FerryFeeHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动渡钱吗？'
