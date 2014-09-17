# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres


__metaclass__ = gen_metafunc(characters.reimu)


class Flight:
    # Skill
    name = u'飞行'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SpiritualAttack:
    name = u'灵击'

    def clickable(g):
        me = g.me

        if not (me.cards or me.showncards): return False

        try:
            act = g.hybrid_stack[-1]
            if act.cond([characters.reimu.SpiritualAttack(me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        assert skill.is_card(characters.reimu.SpiritualAttack)
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择1张手牌！')

        c = acards[0]

        if c.resides_in not in (me.cards, me.showncards):
            return (False, u'只能使用手牌发动！')
        elif not c.color == cards.Card.RED:
            return (False, u'请选择红色手牌！')

        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动使用灵击')

    def sound_effect(act):
        return gres.cv.reimu_sa

    def effect_string(act):
        return cards.RejectCard.ui_meta.effect_string(act)


class TributeTarget:
    # Skill
    name = u'纳奉'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Tribute:
    # Skill
    name = u'塞钱'

    def clickable(game):
        me = game.me

        if limit1_skill_used('tribute_tag'):
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, tl):
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        if len(cl) != 1: return (False, u'只能选择一张手牌')

        if not cl[0].resides_in.type in ('cards', 'showncards'):
            return (False, u'只能选择手牌！')

        if len(tl) != 1 or not tl[0].has_skill(characters.reimu.TributeTarget):
            return (False, u'请选择一只灵梦')

        if len(tl[0].cards) + len(tl[0].showncards) >= tl[0].maxlife:
            return (False, u'灵梦的塞钱箱满了')

        return (True, u'塞钱……会发生什么呢？')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r向|G【%s】|r的塞钱箱里放了一张牌… 会发生什么呢？'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class Reimu:
    # Character
    char_name = u'博丽灵梦'
    port_image = gres.reimu_port
    miss_sound_effect = gres.cv.reimu_miss
    description = (
        u'|DB节操满地跑的城管 博丽灵梦 体力：3|r\n\n'
        u'|G灵击|r：你可以将你的任意一张红色手牌当【好人卡】使用。\n\n'
        u'|G飞行|r：锁定技，当你没有装备任何UFO时，其他玩家对你结算距离时始终+1\n\n'
        u'|DB（画师：Pixiv ID 18697741，CV：shourei小N）|r'
    )
