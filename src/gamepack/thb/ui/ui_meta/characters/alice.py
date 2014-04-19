# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.alice)


class Alice:
    # Character
    char_name = u'爱丽丝'
    port_image = gres.alice_port
    description = (
        u'|DB七色的人偶使 爱丽丝 体力：3|r\n\n'
        u'|G小小军势|r：当你使用装备牌时，你可以摸一张牌。当你失去装备牌区的牌后，你可以弃置其它角色的一张牌。\n\n'
        u'|G少女文乐|r：锁定技，你的手牌上限+X（X为你装备区牌数量的一半，向上取整且至少为1）。\n\n'
        u'|G玩偶十字军|r：出牌阶段，你可以将你的非延时符卡作为【人形操控】使用。每阶段限一次。'
    )


class LittleLegion:
    # Skill
    name = u'小小军势'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LittleLegionDrawCards:
    pass


class LittleLegionAction:
    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G小小军势|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )


class LittleLegionHandler:
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【小小军势】吗？'

    def target(tl):
        if not tl:
            return False, u'小小军势：弃置目标的一张牌'

        tgt = tl[0]

        if tgt.cards or tgt.showncards or tgt.equips:
            return True, u'让你见识一下这人偶军团的厉害！'
        else:
            return False, u'这货已经没有牌了'


class MaidensBunraku:
    # Skill
    name = u'少女文乐'
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
            if limit1_skill_used('alice_doll_tag'):
                return False
        except IndexError:
            return False

        cond = isinstance(act, actions.ActionStage)
        cond = cond and act.target is me
        cond = cond and (me.cards or me.showncards)
        return bool(cond)

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        while True:
            if len(cl) != 1: break
            if 'instant_spellcard' not in cl[0].category: break
            return cards.DollControlCard.ui_meta.is_action_valid(g, [skill], target_list)

        return (False, u'请选择一张非延时符卡！')

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
