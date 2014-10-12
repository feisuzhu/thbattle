# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.ui_meta.common import card_desc, limit1_skill_used
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.kokoro)


class Kokoro:
    # Character
    char_name = u'秦心'
    port_image = gres.kokoro_port
    figure_image = gres.kokoro_figure
    miss_sound_effect = gres.cv.kokoro_miss
    description = (
        u'|DB表情丰富的扑克脸 秦心 体力：3|r\n\n'
        u'|G希望之面|r：出牌阶段开始时。你可以观看牌堆顶1+X张牌，然后展示并获得其中任意数量的同一种花色的牌，其余以任意顺序置于牌堆顶。（X为你已损失的体力值）\n\n'
        u'|G暗黑能乐|r：出牌阶段，你可以将一张黑色牌置于体力不低于你的其他角色的明牌区，该角色需弃置除获得的牌以外的手牌直至手牌数等于其当前体力值。每阶段限一次。\n\n'
        u'|R异变模式不可用|r\n\n'
        u'|DB（画师：Takibi，CV：小羽/VV）|r'
    )


class HopeMask:
    # Skill
    name = u'希望之面'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class HopeMaskHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【希望之面】吗？'


class HopeMaskAction:
    def effect_string_before(act):
        return u'|G【%s】|r挑选面具中……' % (act.source.ui_meta.char_name)

    def effect_string(act):
        if not len(act.acquire):
            return None

        s = u'、'.join([card_desc(c) for c in act.acquire])
        return u'|G【%s】|r拿起了%s，贴在了自己的脸上。' % (
            act.source.ui_meta.char_name, s,
        )

    def sound_effect(act):
        return gres.cv.kokoro_hopemask


class DarkNohAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'真坑！')
        else:
            return (False, u'请弃置%d张手牌（不能包含获得的那一张）' % act.n)


class DarkNoh:
    # Skill
    name = u'暗黑能乐'

    def clickable(game):
        me = game.me
        if limit1_skill_used('darknoh_tag'):
            return False

        if not my_turn():
            return False

        if me.cards or me.showncards or me.equips:
            return True

        return False

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
            u'|G【%s】|r：“这点失控还不够，让你的所有感情也一起爆发吧！”' % source.ui_meta.char_name,
            u'|G【%s】|r使用|G%s|r对|G【%s】|r发动了|G暗黑能乐|r。' % (
                source.ui_meta.char_name,
                card.associated_cards[0].ui_meta.name,
                target.ui_meta.char_name,
            )
        ]

    def sound_effect(act):
        return gres.cv.kokoro_darknoh
