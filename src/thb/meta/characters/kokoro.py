# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Card, Skill
from thb.meta.common import ui_meta, N


# -- code --


@ui_meta(characters.kokoro.Kokoro)
class Kokoro:
    # Character
    name        = '秦心'
    title       = '表情丰富的扑克脸'
    illustrator = 'Takibi'
    cv          = '小羽/VV'

    port_image        = 'thb-portrait-kokoro'
    figure_image      = 'thb-figure-kokoro'
    miss_sound_effect = 'thb-cv-kokoro_miss'


@ui_meta(characters.kokoro.KokoroKOF)
class KokoroKOF:
    # Character
    name        = '秦心'
    title       = '表情丰富的扑克脸'
    illustrator = 'Takibi'
    cv          = '小羽/VV'

    port_image        = 'thb-portrait-kokoro'
    figure_image      = 'thb-figure-kokoro'
    miss_sound_effect = 'thb-cv-kokoro_miss'

    notes = 'KOF修正角色'


@ui_meta(characters.kokoro.HopeMask)
class HopeMask:
    # Skill
    name = '希望之面'
    description = '出牌阶段开始时，你可以观看牌堆顶的1+X张牌，然后展示并获得其中任意数量的同花色牌，其余的牌以任意顺序置于牌堆顶。（X为你已损失的体力值）'


@ui_meta(characters.kokoro.HopeMaskKOF)
class HopeMaskKOF:
    # Skill
    name = '希望之面'
    description = '出牌阶段开始时，你可以观看牌堆顶的X+1张牌，然后展示并获得其中一张牌，其余的牌以任意顺序置于牌堆顶。（X为你已损失的体力值）'


@ui_meta(characters.kokoro.BaseHopeMaskHandler)
class BaseHopeMaskHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>希望之面</style>吗？'


@ui_meta(characters.kokoro.BaseHopeMaskAction)
class BaseHopeMaskAction:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}挑选面具中……'

    def effect_string(self, act):
        if not len(act.acquire):
            return None

        return f'{N.char(act.source)}拿起了{N.card(act.acquire)}，贴在了自己的脸上。'

    def sound_effect(self, act):
        return 'thb-cv-kokoro_hopemask'


@ui_meta(characters.kokoro.BaseDarkNohAction)
class BaseDarkNohAction:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '真坑！')
        else:
            return (False, f'请弃置{act.n}张手牌（不能包含获得的那一张）')


@ui_meta(characters.kokoro.BaseDarkNoh)
class BaseDarkNoh:
    # Skill
    name = '暗黑能乐'

    def is_action_valid(self, sk, tl):
        cl = sk.associated_cards
        if len(cl) != 1 or cl[0].suit not in (Card.SPADE, Card.CLUB):
            return (False, '请选择一张黑色的牌！')

        c = cl[0]
        if c.is_card(Skill):
            return (False, '你不能像这样组合技能')

        return (True, '发动暗黑能乐')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        assoc = card.associated_cards[0]
        return [
            f'{N.char(source)}：“这点失控还不够，让你的所有感情也一起爆发吧！”',
            f'{N.char(source)}使用{N.card(assoc)}对{N.char(target)}发动了{N.card(characters.kokoro.BaseDarkNoh)}。'
        ]

    def sound_effect(self, act):
        return 'thb-cv-kokoro_darknoh'


@ui_meta(characters.kokoro.DarkNoh)
class DarkNoh:
    description = '出牌阶段限一次，你可以将一张黑色牌置于体力值不小于你的其他角色的明牌区，然后其须弃置除获得的牌以外的手牌，直到手牌数与体力值相等。'

    def clickable(self):
        me = self.me
        if self.limit1_skill_used('darknoh_tag'):
            return False

        if not self.my_turn():
            return False

        if me.cards or me.showncards or me.equips:
            return True

        return False


@ui_meta(characters.kokoro.DarkNohKOF)
class DarkNohKOF:
    description = '<style=B>限定技</style>，出牌阶段，你可以将一张黑色牌置于体力值不小于你的其他角色的明牌区，然后其须弃置除获得的牌以外的手牌，直到手牌数与体力值相等。'

    def clickable(self):
        me = self.me
        if me.tags['darknoh_tag'] > 0:
            return False

        if not self.my_turn():
            return False

        if me.cards or me.showncards or me.equips:
            return True

        return False
