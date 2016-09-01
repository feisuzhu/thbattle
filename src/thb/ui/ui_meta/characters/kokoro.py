# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, limit1_skill_used, my_turn
from thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.kokoro)


class Kokoro:
    # Character
    name        = u'秦心'
    title       = u'表情丰富的扑克脸'
    illustrator = u'Takibi'
    cv          = u'小羽/VV'

    port_image        = u'thb-portrait-kokoro'
    figure_image      = u'thb-figure-kokoro'
    miss_sound_effect = u'thb-cv-kokoro_miss'


class KokoroKOF:
    # Character
    name        = u'秦心'
    title       = u'表情丰富的扑克脸'
    illustrator = u'Takibi'
    cv          = u'小羽/VV'

    port_image        = u'thb-portrait-kokoro'
    figure_image      = u'thb-figure-kokoro'
    miss_sound_effect = u'thb-cv-kokoro_miss'

    notes = u'|RKOF修正角色|r'


class HopeMask:
    # Skill
    name = u'希望之面'
    description = u'出牌阶段开始时，你可以观看牌堆顶的1+X张牌，然后展示并获得其中任意数量的同花色牌，其余的牌以任意顺序置于牌堆顶。（X为你已损失的残机数）'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class HopeMaskKOF:
    # Skill
    name = u'希望之面'
    description = u'出牌阶段开始时，你可以观看牌堆顶的X+1张牌，然后展示并获得其中一张牌，其余的牌以任意顺序置于牌堆顶。（X为你已损失的残机数）'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class BaseHopeMaskHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【希望之面】吗？'


class BaseHopeMaskAction:
    def effect_string_before(act):
        return u'|G【%s】|r挑选面具中……' % (act.source.ui_meta.name)

    def effect_string(act):
        if not len(act.acquire):
            return None

        return u'|G【%s】|r拿起了%s，贴在了自己的脸上。' % (
            act.source.ui_meta.name, card_desc(act.acquire),
        )

    def sound_effect(act):
        return 'thb-cv-kokoro_hopemask'


class BaseDarkNohAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'真坑！')
        else:
            return (False, u'请弃置%d张手牌（不能包含获得的那一张）' % act.n)


class BaseDarkNoh:
    # Skill
    name = u'暗黑能乐'

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1 or cl[0].suit not in (cards.Card.SPADE, cards.Card.CLUB):
            return (False, u'请选择一张黑色的牌！')

        c = cl[0]
        if c.is_card(cards.Skill):
            return (False, u'你不能像这样组合技能')

        return (True, u'发动暗黑能乐')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        return [
            u'|G【%s】|r：“这点失控还不够，让你的所有感情也一起爆发吧！”' % source.ui_meta.name,
            u'|G【%s】|r使用|G%s|r对|G【%s】|r发动了|G暗黑能乐|r。' % (
                source.ui_meta.name,
                card.associated_cards[0].ui_meta.name,
                target.ui_meta.name,
            )
        ]

    def sound_effect(act):
        return 'thb-cv-kokoro_darknoh'


class DarkNoh:
    description = u'出牌阶段限一次，你可以将一张黑色牌置于残机数不小于你的其他角色的明牌区，然后其须弃置除获得的牌以外的手牌，直到手牌数与残机数相等。'

    def clickable(g):
        me = g.me
        if limit1_skill_used('darknoh_tag'):
            return False

        if not my_turn():
            return False

        if me.cards or me.showncards or me.equips:
            return True

        return False


class DarkNohKOF:
    description = u'|B限定技|r，出牌阶段，你可以将一张黑色牌置于残机数不小于你的其他角色的明牌区，然后其须弃置除获得的牌以外的手牌，直到手牌数与残机数相等。'

    def clickable(g):
        me = g.me
        if me.tags['darknoh_tag'] > 0:
            return False

        if not my_turn():
            return False

        if me.cards or me.showncards or me.equips:
            return True

        return False
