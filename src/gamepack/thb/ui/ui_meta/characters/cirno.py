# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.actions import ttags
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc, my_turn, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.cirno)


class PerfectFreeze:
    # Skill
    name = u'完美冻结'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CirnoDropCards:
    def effect_string(act):
        return u'|G【%s】|r弃置了|G【%s】|r的%s。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            card_desc(act.cards),
        )


class PerfectFreezeAction:
    def effect_string_before(act):
        return u'|G【%s】|r被冻伤了。' % act.target.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-cirno_perfectfreeze'


class PerfectFreezeHandler:
    choose_option_prompt = u'你要发动【完美冻结】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class Bakadesu:
    # Skill
    name = u'最强'

    def clickable(game):
        me = game.me

        if ttags(me)['bakadesu']:
            return False

        return my_turn()

    def is_action_valid(g, cl, tl):
        if len(tl) != 1:
            return (False, u'请选择嘲讽对象')

        if len(cl[0].associated_cards):
            return (False, u'请不要选择牌！')

        return (True, u'老娘最强！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r双手叉腰，对着|G【%s】|r大喊：“老娘最强！”' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-cirno_perfectfreeze'


class BakadesuAction:
    def choose_card_text(g, act, cl):
        if act.cond(cl):
            return (True, u'啪！啪！啪！')
        else:
            return (False, u'请选择一张弹幕对【%s】使用' % act.source)


class Cirno:
    # Character
    char_name = u'琪露诺'
    port_image = 'thb-portrait-cirno'
    figure_image = 'thb-figure-cirno'
    miss_sound_effect = 'thb-cv-cirno_miss'
    description = (
        u'|DB跟青蛙过不去的笨蛋 琪露诺 体力：4|r\n'
        u'\n'
        u'|G最强|r：出牌阶段限一次，你可以指定一名可以合法对你使用|G弹幕|r的角色，该角色选择一项：\n'
        u'|B|R>> |r对你使用一张|G弹幕|r\n'
        u'|B|R>> |r令你弃置其一张牌\n'
        u'\n'
        u'|G完美冻结|r：当你对一名角色造成伤害时，你可以防止此次伤害并弃置其一张手牌。若此时其手牌数小于其当前体力值，该角色失去一点体力。\n'
        u'\n'
        u'|DB（画师：渚FUN，CV：君寻）|r'
    )
