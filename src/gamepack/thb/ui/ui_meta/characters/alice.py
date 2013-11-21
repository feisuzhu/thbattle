# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.alice)


class Alice:
    # Character
    char_name = u'爱丽丝'
    port_image = gres.alice_port
    description = (
        u'|DB七色的人偶使 爱丽丝 体力：4|r\n\n'
        u'|G人形操演|r：出牌阶段，你可以使用任意数量的【弹幕】。\n\n'
        u'|G玩偶十字军|r：出牌阶段，你可以将你的饰品作为【人形操控】使用。'
    )


class DollManipulation:
    # Skill
    name = u'人形操演'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DollCrusader:
    # Skill
    name = u'玩偶十字军'
    custom_ray = True

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        cond = isinstance(act, actions.ActionStage)
        cond = cond and act.target is me
        cond = cond and (me.cards or me.showncards or me.equips)
        return bool(cond)

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        while True:
            if len(cl) != 1: break
            c = cl[0]
            cat = getattr(c, 'equipment_category', None)
            if cat != 'accessories': break
            return cards.DollControlCard.ui_meta.is_action_valid(g, [skill], target_list)

        return (False, u'请选择一张饰品！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        target = act.target
        s = u'|G【%s】|r突然向|G【%s】|r射出魔法丝线，将她当作玩偶一样玩弄了起来！' % (
            source.ui_meta.char_name,
            target.ui_meta.char_name,
        )
        return s


# ----------
