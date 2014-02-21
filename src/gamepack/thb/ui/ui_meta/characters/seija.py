# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.seija)


class InciteAttack:
    def effect_string(act): pass

class InciteAttackAction:
    def effect_string(act):
        return u'|G【%s】|r在|G【%s】|r的挑拨下对|G【%s】|r使用了|G弹幕|r' % (
            act.source.ui_meta.char_name,
            act.inciter.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class InciteFailAttackAction:
    def effect_string(act):
        return u'|G【%s】|r挑拨|G【%s】|r不成，反而让|G【%s】|r打了上来' % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
            act.source.ui_meta.char_name,
        )

class InciteFailAction:
    def effect_string(act):
        return u'|G【%s】|r想要挑拨|G【%s】|r去攻击|G【%s】|r，但是失败了' % (
            act.inciter.ui_meta.char_name,
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class Incite:
    # Skill
    name = u'挑拨'
    custom_ray = True

    def clickable(game):
        try:
            if limit1_skill_used('incite_tag'):
                return False
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        if not len(tl):
            return (False, u'请选择第一名玩家（【拼点】的对象）')
        elif len(tl) == 1:
            return (False, u'请选择第二名玩家（【弹幕】的目标）')
        else:
            return (True, u'挑拨！')

    def effect_string(act): pass

class InciteAction:
    def ray(act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]

    # choose_option
    choose_option_buttons = ((u'使用', True), (u'不使用', False))
    def choose_option_prompt(act):
        return u'你要对【%s】使用【弹幕】吗？' % act.source.ui_meta.char_name


class Reversal:
    # Skill
    name = u'逆转'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ReversalDuel:
    name = u'逆转'

    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r使用了|G弹幕战|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class ReversalHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【逆转】吗？'


class Seija:
    # Character
    char_name = u'鬼人正邪'
    port_image = gres.seija_port
    description = (
        u'|DB逆袭的天邪鬼 鬼人正邪 体力：3|r\n\n'
        u'|G挑拨|r：出牌阶段，你可以与一名角色拼点，若你赢，视为该角色对其攻击范围内一名由你指定的角色使用了一张【弹幕】。若你没赢，该角色可以视为对你使用了一张【弹幕】。每阶段限一次。\n\n'
        u'|G逆转|r：你于回合外成为一名角色使用的【弹幕】的目标时，你可以摸一张牌，然后若此时你的手牌数大于该角色，此弹幕对你无效并视为该角色对你使用了一张【弹幕战】。'
    )
