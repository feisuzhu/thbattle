# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Skill
from thb.meta.common import G, my_turn, passive_clickable, passive_is_action_valid, ui_meta


# -- code --


@ui_meta(characters.seiga.Seiga)
class Seiga:
    # Character
    name        = '霍青娥'
    title       = '僵尸别跑'
    illustrator = '和茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-seiga'
    figure_image      = 'thb-figure-seiga'
    miss_sound_effect = 'thb-cv-seiga_miss'


@ui_meta(characters.seiga.SeigaKOF)
class SeigaKOF:
    # Character
    name        = '霍青娥'
    title       = '僵尸别跑'
    illustrator = '和茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-seiga'
    figure_image      = 'thb-figure-seiga'
    miss_sound_effect = 'thb-cv-seiga_miss'

    notes = '|RKOF修正角色'


@ui_meta(characters.seiga.HeterodoxyHandler)
class HeterodoxyHandler:
    # choose_option meta
    choose_option_buttons = (('跳过结算', True), ('正常结算', False))
    choose_option_prompt = '你要跳过当前的卡牌结算吗？'


@ui_meta(characters.seiga.HeterodoxySkipAction)
class HeterodoxySkipAction:
    def effect_string(self, act):
        return '|G【%s】|r跳过了卡牌效果的结算' % (
            act.source.ui_meta.name,
        )


@ui_meta(characters.seiga.HeterodoxyAction)
class HeterodoxyAction:
    def ray(self, act):
        return [(act.source, act.target_list[0])]


@ui_meta(characters.seiga.Heterodoxy)
class Heterodoxy:
    # Skill
    name = '邪仙'
    description = (
        '出牌阶段，你可以将一张手牌以一名其他角色的身份使用。\n'
        '|B|R>> |r以此法使用|G弹幕|r消耗你的干劲\n'
        '|B|R>> |r你成为此法使用的群体符卡的目标后，可以跳过此次结算。'
    )
    custom_ray = True

    def clickable(self, g):
        if not my_turn(): return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def effect_string(self, act):
        return '|G【%s】|r发动了邪仙技能，以|G【%s】|r的身份使用了卡牌' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def is_action_valid(self, g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, '请选择一张手牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards'):
            return (False, '请选择一张手牌!')

        if card.is_card(Skill):
            return (False, '你不可以像这样组合技能')

        if not getattr(card, 'associated_action', None):
            return (False, '请的选择可以主动发动的卡牌！')

        if not tl:
            return (False, '请选择一名玩家作为卡牌发起者')

        victim = tl[0]
        _tl, valid = card.target(g, victim, tl[1:])
        return card.ui_meta.is_action_valid(g, [card], _tl)

        # can't reach here
        # return (True, u'僵尸什么的最萌了！')
        # orig

    def sound_effect(self, act):
        return 'thb-cv-seiga_heterodoxy'


@ui_meta(characters.seiga.Summon)
class Summon:
    # Skill
    name = '通灵'
    description = '|B限定技|r，你的回合内，当有角色被击坠时，你可以获得其一个技能（不包括限定技，觉醒技）'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.seiga.SummonAction)
class SummonAction:
    # choose_option meta
    choose_option_prompt = '请选择想要获得的技能：'

    def choose_option_buttons(self, act):
        return [
            (s.ui_meta.name, n)
            for n, s in act.mapping.items()
        ]

    def ray(self, act):
        return [(act.source, act.target)]

    def effect_string(self, act):
        return '|G【%s】|r发动了|G通灵|r，获得了|G【%s】|r的|G%s|r技能' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            act.choice.ui_meta.name,
        )


@ui_meta(characters.seiga.SummonHandler)
class SummonHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【通灵】吗？'


@ui_meta(characters.seiga.SummonKOF)
class SummonKOF:
    # Skill
    name = '通灵'
    description = (
        '你可以将击坠角色的角色牌加入你的备选角色；出牌阶段，你可以和你的备选角色交换角色牌，然后结束出牌阶段。\n'
        '|B|R>> |r你的体力值保留，体力上限会调整到与新角色一致。'
    )

    def clickable(self, g):
        return my_turn()

    def is_action_valid(self, g, cl, target_list):
        cl = cl[0].associated_cards
        if len(cl) != 0:
            return False, '请不要选择牌'

        rest = '、'.join([c.char_cls.ui_meta.name for c in G().me.choices])
        return True, '通灵：后备角色：%s' % rest

    def effect_string(self, act):
        return '|G【%s】|r发动了|G通灵|r！' % (
            act.source.ui_meta.name,
        )


@ui_meta(characters.seiga.SummonKOFAction)
class SummonKOFAction:

    def effect_string(self, act):
        old, new = act.transition
        return '|G【%s】|r召唤了|G【%s】|r，自己退居幕后！' % (
            old.ui_meta.name,
            new.ui_meta.name,
        )


@ui_meta(characters.seiga.SummonKOFCollect)
class SummonKOFCollect:

    def effect_string_before(self, act):
        src, tgt = act.source, act.target
        return '|G【%s】|r把|G【%s】|r做成了僵尸宠物！' % (
            src.ui_meta.name,
            tgt.ui_meta.name,
        )
