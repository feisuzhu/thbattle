# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Skill
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.sp_aya.WindWalk)
class WindWalk:
    # Skill
    name = '疾走'
    description = '出牌阶段，你可以弃置一张牌，然后摸一张牌，对你上一张使用的牌的目标角色（或之一）使用之并重复此流程，否则结束你的回合。'

    def clickable(self):
        if not self.my_turn():
            return False

        me = self.me
        return bool(me.cards or me.showncards or me.equips)

    def is_action_valid(self, sk, tl):
        acards = sk.associated_cards
        if (not acards) or len(acards) != 1:
            return (False, '请选择一张牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards', 'equips'):
            return (False, '请选择一张牌!')

        if card.is_card(Skill):
            return (False, '你不可以像这样组合技能')

        return (True, '疾走')

    def effect_string(self, act):
        return f'唯快不破！{N.char(act.source)}弃置了{N.card(act.card)}，开始加速追击！'

    def sound_effect(self, act):
        return 'thb-cv-sp_aya_windwalk'


@ui_meta(characters.sp_aya.WindWalkLaunch)
class WindWalkLaunch:
    pass


@ui_meta(characters.sp_aya.WindWalkAction)
class WindWalkAction:
    idle_prompt = '疾走：请使用摸到的牌（否则结束出牌并跳过弃牌阶段）'

    def choose_card_text(self, act, cards):
        if not act.cond(cards):
            return False, '疾走：只能使用摸到的牌（或者结束）'
        else:
            return True, '不会显示……'


@ui_meta(characters.sp_aya.WindWalkSkipAction)
class WindWalkSkipAction:
    def effect_string_before(self, act):
        return f'{N.char(act.target)}放弃了追击。'

    def sound_effect(self, act):
        return 'thb-cv-sp_aya_windwalk_stop'


@ui_meta(characters.sp_aya.WindWalkTargetLimit)
class WindWalkTargetLimit:
    # target_independent = True
    shootdown_message = '你只能对上一张使用的牌的目标角色（或之一）使用。'


@ui_meta(characters.sp_aya.DominanceHandler)
class DominanceHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>风靡</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(characters.sp_aya.DominanceAction)
class DominanceAction:
    def effect_string_before(self, act):
        return f'{N.char(act.target)}成功地了搞了个大新闻！'

    def sound_effect(self, act):
        return 'thb-cv-sp_aya_dominance'


@ui_meta(characters.sp_aya.Dominance)
class Dominance:
    # Skill
    name = '风靡'
    description = '回合结束时，若你本回合的出牌阶段使用了四种花色的牌，你可执行一个额外的回合。'


@ui_meta(characters.sp_aya.SpAya)
class SpAya:
    # Character
    name        = 'SP射命丸文'
    title       = '剑圣是谁有我快吗'
    designer    = '吹风姬'
    illustrator = '躲猫'
    cv          = '君寻'

    port_image        = 'thb-portrait-sp_aya'
    figure_image      = 'thb-figure-sp_aya'
    miss_sound_effect = 'thb-cv-sp_aya_miss'
