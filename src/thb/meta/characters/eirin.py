# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import N, ui_meta


# -- code --
@ui_meta(characters.eirin.SkySilk)
class SkySilk:
    # Skill
    name = '天丝'
    description = (
        '出牌阶段限一次，你可以弃置一名角色的一张牌，并令其选择一项：'
        '<style=Desc.Li>回复1点体力。</style>'
        '<style=Desc.Li>展示牌堆底的3张牌，获得其中的非基本牌，并弃置其他的牌。</style>'
    )

    def clickable(self):
        me = self.me
        if not self.my_turn() or actions.ttags(me)['sky_silk']:
            return False

        return True

    def is_action_valid(g, sk, tl):
        cl = sk.associated_cards
        if cl:
            return False, '请不要选择牌！'

        return True, '发动<style=Skill.Name>天丝</style>'

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'{N.char(act.source)}对{N.char(act.target)}发动了<style=Skill.Name>天丝</style>。'

    def sound_effect(self, act):
        return 'thb-cv-eirin_medic'


@ui_meta(characters.eirin.SkySilkAction)
class SkySilkAction:
    # choose_option
    choose_option_buttons = (('回复', 'heal'), ('摸牌', 'draw'))
    choose_option_prompt = '选择你要发动的效果'

    def drop_cards_tip(self, trans: actions.MigrateCardsTransaction) -> str:
        return '<style=Skill.Name>天丝</style>弃牌'


@ui_meta(characters.eirin.LunaString)
class LunaString:
    name = '月弦'
    description = '你可以将一张手牌置于牌堆顶或牌堆底底，视为使用或打出了一张<style=Card.Name>弹幕</style>。以此法使用牌时，每回合限一次。'

    def clickable(self):
        return self.accept_cards([characters.eirin.LunaString(self.me)])

    def is_complete(self, sk):
        from thb.cards.base import VirtualCard

        s = N.skill(characters.eirin.LunaString)

        acards = sk.associated_cards
        if len(acards) != 1:
            return False, '请选择一张手牌'

        c = acards[0]

        if c.resides_in.type not in ('cards', 'showncards'):
            return False, '请选择一张手牌'

        if c.is_card(VirtualCard):
            return False, f'{s}不允许组合使用'

        return True, f'发动{s}'

    def is_action_valid(self, sk, tl):
        from thb.cards.classes import AttackCard

        isc, t = self.is_complete(sk)
        if not isc:
            return isc, t

        c = sk.associated_cards[0]
        if actions.ttags(self.me)['luna_string_used']:
            s = N.skill(characters.eirin.LunaString)
            return False, f'{s}只能每回合使用一次'

        return AttackCard().ui_meta.is_action_valid(c, tl)


@ui_meta(characters.eirin.LunaStringPlaceCard)
class LunaStringPlaceCard:
    # choose_option
    choose_option_buttons = (('牌堆顶↑', 'front'), ('牌堆底↓', 'back'))
    choose_option_prompt = '你要把牌放到哪里'

    def effect_string(self, act):
        if act.direction == 'front':
            return '阴谋！有人注意到牌堆上面的牌变了吗？'
        else:
            return '阴谋！有人注意到牌堆好像比原来高了一点吗？'


@ui_meta(characters.eirin.Eirin)
class Eirin:
    # Character
    name        = '八意永琳'
    title       = '伪月主谋'
    illustrator = '渚FUN'
    cv          = 'VV'

    miss_sound_effect = 'thb-cv-eirin_miss'

    notes = 'KOF不平衡角色'
