# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import cast

# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta
from utils.misc import BatchList
import thb.cards.classes as cards


# -- code --
@ui_meta(characters.chen.FlyingSkanda)
class FlyingSkanda:
    # Skill
    name = '飞翔韦驮天'
    description = (
        '出牌阶段限一次，你使用|G弹幕|r或单体符卡时，可以额外指定一个目标。\n'
        '|B|R>> |r在线版本中，不能以此法使用|G人形操控|r'
    )

    def clickable(self):
        g = self.game
        me = self.me
        if me.tags['flying_skanda'] >= me.tags['turn_count']: return False
        try:
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(self, sk, tl):
        acards = sk.associated_cards
        if len(acards) != 1:
            return (False, '请选择一张牌！')
        c = acards[0]

        while True:
            if c.is_card(cards.AttackCard): break

            rst = True
            rst = rst and not c.is_card(cards.RejectCard)
            rst = rst and not c.is_card(cards.DollControlCard)
            rst = rst and c.associated_action
            rst = rst and issubclass(c.associated_action, cards.InstantSpellCardAction)
            if rst: break

            return (False, '请选择一张【弹幕】或者除【人形操控】与【好人卡】之外的非延时符卡！')

        if len(tl) != 2:
            return (False, '请选择目标（2名玩家）')

        if self.me is tl[-1]:
            return (False, '不允许选择自己')
        else:
            return (True, '喵！')

    def effect_string(self, act: actions.LaunchCard):
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        card = cast(characters.chen.FlyingSkanda, act.card).associated_cards[0]
        tl = BatchList(act.target_list)

        if card.is_card(cards.AttackCard):
            s = '弹幕掺了金坷垃，攻击范围一千八！'
        else:
            s = '符卡掺了金坷垃，一张能顶两张用！'

        return '|G【%s】|r：“%s|G【%s】|r接招吧！”' % (
            src.ui_meta.name,
            s,
            '】|r、|G【'.join(tl.ui_meta.name),
        )

    def sound_effect(self, act):
        return 'thb-cv-chen_skanda'


@ui_meta(characters.chen.Shikigami)
class Shikigami:
    # Skill
    name = '式神'
    description = (
        '|B限定技|r，出牌阶段，你可以令一名其他角色选择一项：|B|R>> |r摸两张牌，|B|R>> |r回复1点体力。\n'
        '直到下次你的回合开始时，你与其可以在出牌阶段对对方攻击范围内的角色使用|G弹幕|r。'
    )

    def clickable(self):
        g = self.game
        me = self.me
        if me.tags.get('shikigami_tag'): return False
        try:
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(self, sk, tl):
        cl = sk.associated_cards
        if cl:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '请选择一名玩家')
        else:
            return (True, '发动【式神】')

    def sound_effect(self, act):
        return 'thb-cv-chen_shikigami'


@ui_meta(characters.chen.ShikigamiAction)
class ShikigamiAction:
    choose_option_buttons = (('摸2张牌', False), ('回复1点体力', True))
    choose_option_prompt = '请为受到的【式神】选择效果'


@ui_meta(characters.chen.Chen)
class Chen:
    name        = '橙'
    title       = '凶兆的黑喵'
    illustrator = '和茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-chen'
    figure_image      = 'thb-figure-chen'
    miss_sound_effect = 'thb-cv-chen_miss'
