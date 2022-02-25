# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING

# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Skill
from thb.meta.common import ui_meta, N

# -- typing --
if TYPE_CHECKING:
    from thb.thbkof import THBattleKOF  # noqa: F401


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

    notes = 'KOF修正角色'


@ui_meta(characters.seiga.HeterodoxyHandler)
class HeterodoxyHandler:
    # choose_option meta
    choose_option_buttons = (('跳过结算', True), ('正常结算', False))
    choose_option_prompt = '你要跳过当前的卡牌结算吗？'


@ui_meta(characters.seiga.HeterodoxySkipAction)
class HeterodoxySkipAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}跳过了卡牌效果的结算'


@ui_meta(characters.seiga.HeterodoxyAction)
class HeterodoxyAction:
    def ray(self, act):
        return [(act.source, act.target_list[0])]


@ui_meta(characters.seiga.Heterodoxy)
class Heterodoxy:
    # Skill
    name = '邪仙'
    description = (
        '出牌阶段，你可以将一张手牌以一名其他角色的身份使用。'
        '<style=Desc.Li>以此法使用<style=Card.Name>弹幕</style>消耗你的干劲。</style>'
        '<style=Desc.Li>你成为此法使用的群体符卡的目标后，可以跳过此次结算。</style>'
    )
    custom_ray = True

    def clickable(self):
        if not self.my_turn(): return False
        me = self.me
        return bool(me.cards or me.showncards or me.equips)

    def effect_string(self, act):
        return f'{N.char(act.source)}发动了邪仙技能，以{N.char(act.target)}的身份使用了卡牌'

    def is_action_valid(self, sk, tl):
        acards = sk.associated_cards
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
        _tl, valid = card.target(victim, tl[1:])
        return card.ui_meta.is_action_valid([card], _tl)

        # can't reach here
        # return (True, u'僵尸什么的最萌了！')
        # orig

    def sound_effect(self, act):
        return 'thb-cv-seiga_heterodoxy'


@ui_meta(characters.seiga.Summon)
class Summon:
    # Skill
    name = '通灵'
    description = '<style=B>限定技</style>，你的回合内，当有角色被击坠时，你可以获得其一个技能。（不包括限定技，觉醒技）'

    def is_available(self, ch):
        return bool(ch.tags['summon_used'])


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
        return f'{N.char(act.source)}发动了<style=Skill.Name>通灵</style>，获得了{N.char(act.target)}的{N.card(act.choice)}技能。'


@ui_meta(characters.seiga.SummonHandler)
class SummonHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>通灵</style>吗？'


@ui_meta(characters.seiga.SummonKOF)
class SummonKOF:
    game: THBattleKOF

    # Skill
    name = '通灵'
    description = (
        '你可以将击坠角色的角色牌加入你的备选角色；出牌阶段，你可以和你的备选角色交换角色牌，然后结束出牌阶段。'
        '<style=Desc.Attention>你的体力值保留，体力上限会调整到与新角色一致。</style>'
    )

    def clickable(self):
        return self.my_turn()

    def is_action_valid(self, sk, tl):
        g = self.game
        me = self.me
        cl = sk.associated_cards
        if len(cl) != 0:
            return False, '请不要选择牌'

        rest = N.char([c.char_cls for c in g.chosen[me.player] if c.char_cls])
        return True, f'通灵：后备角色：{rest}'

    def effect_string(self, act):
        return f'{N.char(act.source)}发动了<style=Skill.Name>通灵</style>！'


@ui_meta(characters.seiga.SummonKOFAction)
class SummonKOFAction:

    def effect_string(self, act):
        old, new = act.transition
        return f'{N.char(old)}召唤了{N.char(new)}，自己退居幕后！'


@ui_meta(characters.seiga.SummonKOFCollect)
class SummonKOFCollect:

    def effect_string_before(self, act):
        src, tgt = act.source, act.target
        return f'{N.char(src)}把{N.char(tgt)}做成了僵尸宠物！'
