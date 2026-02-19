# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Skill
from thb.meta.common import ui_meta, N


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
    description = '出牌阶段限一次，你可以弃置一张牌并指定一名其他角色，你与其距离视为1直到回合结束，然后若该角色的体力为全场最少的（或之一），你选择一项：<style=Desc.Li>摸一张牌</style><style=Desc.Li>弃置其一张牌</style>'

    def clickable(self):
        me = self.me
        if not self.my_turn(): return False
        if self.limit1_skill_used('riverside_tag'): return False

        return bool(me.cards or me.showncards or me.equips)

    def is_action_valid(self, sk, tl):
        acards = sk.associated_cards
        if (not acards) or len(acards) != 1:
            return (False, '请选择一张牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards', 'equips'):
            return (False, 'WTF?!')

        if card.is_card(Skill):
            return (False, '你不可以像这样组合技能')

        return (True, '近一点~再近一点~~')

    def effect_string(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}使用了<style=Skill.Name>彼岸</style>。'

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
        return f'{N.char(act.target)}：“啊啊不能再偷懒啦！要被四季大人说教啦！”'

    def sound_effect(self, act):
        return 'thb-cv-komachi_awake'


@ui_meta(characters.komachi.Returning)
class Returning:
    # Skill
    name = '归航'
    description = (
        '<style=B>觉醒技</style>，准备阶段开始时，若你体力小于手牌数且不大于2，你减1点体力上限并获得技能<style=Skill.Name>渡钱</style>。'
        '<style=Desc.Li><style=Skill.Name>渡钱</style>：每当你对距离1的其他角色造成伤害后，你可以获得其一张牌。</style>'
    )


@ui_meta(characters.komachi.FerryFee)
class FerryFee:
    # Skill
    name = '渡钱'
    description = '每当你对距离1的其他角色造成伤害后，你可以获得其一张牌。'


@ui_meta(characters.komachi.FerryFeeEffect)
class FerryFeeEffect:
    def effect_string(self, act):
        return f'{N.char(act.source)}收走了{N.char(act.target)}的{N.char(act.card)}作为<style=Skill.Name>渡钱</style>。'

    def sound_effect(self, act):
        return 'thb-cv-komachi_ferryfee'


@ui_meta(characters.komachi.FerryFeeHandler)
class FerryFeeHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>渡钱</style>吗？'
