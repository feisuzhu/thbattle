# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.ran.Prophet)
class Prophet:
    # Skill
    name = '神算'
    description = '准备阶段开始时，你可以观看牌堆顶的X张牌，将其中任意数量的牌以任意顺序置于牌堆顶，其余以任意顺序置于牌堆底。（X为存活角色数且至多为5）'


@ui_meta(characters.ran.ExtremeIntelligence)
class ExtremeIntelligence:
    # Skill
    name = '极智'
    description = '每轮限一次，你的回合外，当非延时符卡效果对一名角色生效后，你可以弃置一张牌，令该符卡效果对那名角色重新进行一次结算，此时使用者视为你。'

    def is_available(self, ch):
        return ch.tags['ran_ei'] < ch.tags['turn_count'] + 1


@ui_meta(characters.ran.ExtremeIntelligenceKOF)
class ExtremeIntelligenceKOF:
    # Skill
    name = '极智'
    description = '出牌阶段限一次，你可以将一张手牌当你本回合上一张使用过的非延时符卡使用。'

    def clickable(self):
        me = self.me

        if not (self.my_turn() and (me.cards or me.showncards)):
            return False

        if ttags(me)['ran_eikof_tag']:
            return False

        if not ttags(me)['ran_eikof_card']:
            return False

        return True

    def is_action_valid(self, sk, tl):
        me = self.me
        assert sk.is_card(characters.ran.ExtremeIntelligenceKOF)

        cl = sk.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张牌！')

        if cl[0].resides_in not in (me.cards, me.showncards):
            return (False, '请选择手牌！')

        return sk.treat_as().ui_meta.is_action_valid(sk, tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        src, tl, sk = act.source, act.target_list, act.card
        card = sk.associated_cards[0]
        s = f'{N.char(src)}发动了<style=Skill.Name>极智</style>技能，将{N.card(card)}当作{N.char(sk.treat_as)}对{N.char(tl)}使用。'
        return s


@ui_meta(characters.ran.ProphetHandler)
class ProphetHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>神算</style>吗？'


@ui_meta(characters.ran.ProphetAction)
class ProphetAction:
    def effect_string_before(self, act):
        return f'众人正准备接招呢，{N.char(act.target)}却掐着指头算了起来…'

    def sound_effect(self, act):
        return 'thb-cv-ran_prophet'


@ui_meta(characters.ran.ExtremeIntelligenceAction)
class ExtremeIntelligenceAction:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '再来！')
        else:
            return (False, '弃置1张牌并发动<style=Skill.Name>极智</style>')

    def effect_string_before(self, act):
        return f'{N.char(act.target)}刚松了一口气，却看见一张一模一样的符卡从{N.char(act.source)}的方向飞来！'

    def sound_effect(self, act):
        return 'thb-cv-ran_ei'


@ui_meta(characters.ran.NakedFox)
class NakedFox:
    # Skill
    name = '素裸'
    description = '<style=B>锁定技</style>，若你没有手牌，符卡对你造成的伤害-1。'


@ui_meta(characters.ran.NakedFoxAction)
class NakedFoxAction:
    def effect_string_before(self, act):
        tgt = act.target
        if act.dmgamount <= 1:
            return f'符卡飞到了{N.char(tgt)}毛茸茸的大尾巴里，然后……就没有然后了……'
        else:
            return f'符卡飞到了{N.char(tgt)}毛茸茸的大尾巴里，恩……似乎还是有点疼……'


@ui_meta(characters.ran.Ran)
class Ran:
    # Character
    name        = '八云蓝'
    title       = '天河一号的核心'
    illustrator = '霏茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-ran'
    figure_image      = 'thb-figure-ran'
    miss_sound_effect = 'thb-cv-ran_miss'


@ui_meta(characters.ran.RanKOF)
class RanKOF:
    # Character
    name        = '八云蓝'
    title       = '天河一号的核心'
    illustrator = '霏茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-ran'
    figure_image      = 'thb-figure-ran'
    miss_sound_effect = 'thb-cv-ran_miss'

    notes = 'KOF修正角色'
