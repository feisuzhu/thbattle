# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import cards, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.seiga)


class Seiga:
    # Character
    char_name = u'霍青娥'
    port_image = 'thb-portrait-seiga'
    figure_image = 'thb-figure-seiga'
    miss_sound_effect = 'thb-cv-seiga_miss'
    description = (
        u'|DB僵尸别跑 霍青娥 体力：4|r\n\n'
        u'|G邪仙|r：出牌阶段，你可以将一张可以主动发动的手牌，在合法的情况下，以一名其他玩家的身份使用。\n'
        u'|B|R>> |r以此法使用|G弹幕|r时，弹幕的“一回合一次”的限制由你来承担\n'
        u'|B|R>> |r当你成为以此法使用的群体符卡的目标时，你可以选择跳过此次结算。\n\n'
        u'|G通灵|r：|B限定技|r，你可以获得于你回合内死亡角色的一个技能（不包括限定技，觉醒技和主公技）。\n\n'
        u'|DB（画师：和茶，CV：小羽）|r'
    )


class HeterodoxyHandler:
    # choose_option meta
    choose_option_buttons = ((u'跳过结算', True), (u'正常结算', False))
    choose_option_prompt = u'你要跳过当前的卡牌结算吗？'


class HeterodoxySkipAction:
    def effect_string(act):
        return u'|G【%s】|r跳过了卡牌效果的结算' % (
            act.source.ui_meta.char_name,
        )


class HeterodoxyAction:
    def ray(act):
        return [(act.source, act.target_list[0])]


class Heterodoxy:
    # Skill
    name = u'邪仙'
    custom_ray = True

    def clickable(g):
        if not my_turn(): return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def effect_string(act):
        return u'|G【%s】|r发动了邪仙技能，以|G【%s】|r的身份使用了卡牌' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def is_action_valid(g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, u'请选择一张手牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards'):
            return (False, u'请选择一张手牌!')

        if card.is_card(cards.Skill):
            return (False, u'你不可以像这样组合技能')

        if not getattr(card, 'associated_action', None):
            return (False, u'请的选择可以主动发动的卡牌！')

        if not tl:
            return (False, u'请选择一名玩家作为卡牌发起者')

        victim = tl[0]
        _tl, valid = card.target(g, victim, tl[1:])
        return card.ui_meta.is_action_valid(g, [card], _tl)

        # can't reach here
        # return (True, u'僵尸什么的最萌了！')
        # orig

    def sound_effect(act):
        return 'thb-cv-seiga_heterodoxy'


class Summon:
    # Skill
    name = u'通灵'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SummonAction:
    # choose_option meta
    choose_option_prompt = u'请选择想要获得的技能：'

    def choose_option_buttons(act):
        return [
            (s.ui_meta.name, n)
            for n, s in act.mapping.items()
        ]

    def ray(act):
        return [(act.source, act.target)]

    def effect_string(act):
        return u'|G【%s】|r发动了|G通灵|r，以获得了|G【%s】|r的%s技能' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.choice.ui_meta.name,
        )


class SummonHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【通灵】吗？'
