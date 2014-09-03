# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.sakuya)


class Sakuya:
    # Character
    char_name = u'十六夜咲夜'
    port_image = gres.sakuya_port
    description = (
        u'|DB完全潇洒的PAD长 十六夜咲夜 体力：4|r\n\n'
        u'|G月时计|r：|B锁定技|r，在你的判定阶段开始前，你执行一个额外的出牌阶段。\n\n'
        u'|G飞刀|r：你可以将一张装备牌当【弹幕】使用或打出。你以此法使用【弹幕】时无距离限制。\n\n'
        u'|DB（画师：Danbooru post 137925）|r'
    )


class FlyingKnife:
    # Skill
    name = u'飞刀'

    def clickable(g):
        me = g.me

        if not (me.cards or me.showncards or me.equips): return False

        try:
            act = g.hybrid_stack[-1]
            if act.cond([characters.sakuya.FlyingKnife(me)]):
                act = g.action_stack[-1]
                if act.target is g.me:
                    return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        assert skill.is_card(characters.sakuya.FlyingKnife)
        cl = skill.associated_cards
        if len(cl) != 1 or not issubclass(cl[0].associated_action, cards.WearEquipmentAction):
            return (False, u'请选择一张装备牌！')
        return (True, '快看！灰出去了！')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        rst, reason = is_complete(g, cl)
        if not rst:
            return rst, reason
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, cl, target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r将|G%s|r制成了|G飞刀|r，向|G【%s】|r掷去！' % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.char_name,
        )
        return s


class LunaClock:
    # Skill
    name = u'月时计'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
