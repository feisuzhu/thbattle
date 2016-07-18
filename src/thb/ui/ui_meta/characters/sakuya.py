# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.sakuya)


class Sakuya:
    # Character
    name        = u'十六夜咲夜'
    title       = u'完全潇洒的PAD长'
    illustrator = u'和茶'
    cv          = u'VV'

    port_image        = u'thb-portrait-sakuya'
    figure_image      = u'thb-figure-sakuya'
    miss_sound_effect = u'thb-cv-sakuya_miss'


class Dagger:
    # Skill
    name = u'飞刀'
    description = u'你可以将一张装备牌当|G弹幕|r使用或打出。按此法使用的|G弹幕|r无距离限制。'

    def clickable(g):
        me = g.me

        if not (me.cards or me.showncards or me.equips): return False

        try:
            act = g.hybrid_stack[-1]
            if act.cond([characters.sakuya.Dagger(me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        assert skill.is_card(characters.sakuya.Dagger)
        cl = skill.associated_cards
        if len(cl) != 1 or 'equipment' not in cl[0].category:
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
            source.ui_meta.name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.name,
        )
        return s

    def sound_effect(act):
        return random.choice([
            'thb-cv-sakuya_dagger1',
            'thb-cv-sakuya_dagger2',
        ])


class LunaDialActionStage:
    def sound_effect(act):
        return 'thb-cv-sakuya_lunadial'


class LunaDial:
    # Skill
    name = u'月时计'
    description = u'|B锁定技|r，准备阶段开始时，你执行一个额外的出牌阶段。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
