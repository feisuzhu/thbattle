# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta


# -- code --
@ui_meta(characters.eirin.SkySilk)
class SkySilk:
    # Skill
    name = '天丝'
    description = (
        '出牌阶段限一次，你可以弃置一名角色的一张牌，并令其选择一项：\n'
        '|B|R>> |r回复1点体力。\n'
        '|B|R>> |r展示牌堆底的3张牌，获得其中的非基本牌，并弃置其他的牌。'
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

        return True, '发动「天丝」'

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return (
            '|G【%s】|r对|G【%s】|r发动了「天丝」。'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-eirin_medic'


@ui_meta(characters.eirin.SkySilkAction)
class SkySilkAction:
    # choose_option
    choose_option_buttons = (('回复', 'heal'), ('摸牌', 'draw'))
    choose_option_prompt = '选择你要发动的效果'


@ui_meta(characters.eirin.LunaString)
class LunaString:
    name = '月弦'
    description = '你可以将一张手牌置于牌堆顶或牌堆底底，视为使用或打出了一张|G弹幕|r。'

    def clickable(self):
        g = self.game
        me = self.me
        try:
            act = g.hybrid_stack[-1]
            if act.cond and act.cond([characters.eirin.LunaString(me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(self, sk):
        from thb.cards.base import VirtualCard

        acards = sk.associated_cards
        if len(acards) != 1:
            return False, '请选择一张手牌'

        c = acards[0]

        if c.resides_in.type not in ('cards', 'showncards'):
            return False, '请选择一张手牌'

        if c.is_card(VirtualCard):
            return False, '「月弦」不允许组合使用'

        return True, '发动「月弦」'

    def is_action_valid(self, sk, tl):
        from thb.cards.classes import AttackCard

        isc, t = self.is_complete(sk)
        if not isc:
            return isc, t
        c = sk.associated_cards[0]
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

    port_image        = 'thb-portrait-eirin'
    figure_image      = 'thb-figure-eirin'
    miss_sound_effect = 'thb-cv-eirin_miss'

    notes = u'|RKOF不平衡角色|r'
