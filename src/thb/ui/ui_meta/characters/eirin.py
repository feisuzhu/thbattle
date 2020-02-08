# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters, cards
from thb.ui.ui_meta.common import gen_metafunc, my_turn

# -- code --
__metaclass__ = gen_metafunc(characters.eirin)


class SkySilk:
    # Skill
    name = u'天丝'
    description = (
        u'出牌阶段限一次，你可以弃置一名角色的一张牌，并令其选择一项：\n'
        u'|B|R>> |r回复1点体力\n'
        u'|B|R>> |r展示牌堆底的3张牌，获得其中的非基本牌并弃置其他的牌'
    )

    def clickable(game):
        me = game.me
        if not my_turn() or actions.ttags(me)['sky_silk']:
            return False

        return True

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return False, u'请不要选择牌！'

        return True, u'发动「天丝」'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r对|G【%s】|r发动了「天丝」。'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-eirin_medic'


class SkySilkAction:
    # choose_option
    choose_option_buttons = ((u'回复', 'heal'), (u'摸牌', 'draw'))
    choose_option_prompt = u'选择你要发动的效果'


class LunaString:
    name = u'月弦'
    description = u'你可以将一张手牌置于牌堆顶或牌堆底底，视为使用或打出了一张|G弹幕|r。'

    def clickable(g):
        try:
            act = g.hybrid_stack[-1]
            if act.cond and act.cond([characters.eirin.LunaString(g.me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(g, cl):
        sk = cl[0]
        acards = sk.associated_cards
        if len(acards) != 1:
            return False, u'请选择一张手牌'

        c = acards[0]

        if c.resides_in.type not in ('cards', 'showncards'):
            return False, u'请选择一张手牌'

        if c.is_card(cards.VirtualCard):
            return False, u'「月弦」不允许组合使用'

        return True, u'发动「月弦」'

    def is_action_valid(g, cl, tl, is_complete=is_complete):
        sk = cl[0]
        isc, t = is_complete(g, cl)
        if not isc:
            return isc, t
        c = sk.associated_cards[0]
        return cards.AttackCard.ui_meta.is_action_valid(g, [c], tl)


class LunaStringPlaceCard:
    # choose_option
    choose_option_buttons = ((u'牌堆顶↑', 'top'), (u'牌堆底↓', 'bottom'))
    choose_option_prompt = u'你要把牌放到哪里'

    def effect_string(act):
        if act.place == 'top':
            return u'阴谋！有人注意到牌堆上面的牌变了吗？'
        else:
            return u'阴谋！有人注意到牌堆好像比原来高了一点吗？'


class Eirin:
    # Character
    name        = u'八意永琳'
    title       = u'伪月主谋'
    illustrator = u'渚FUN'
    cv          = u'VV'

    port_image        = u'thb-portrait-eirin'
    figure_image      = u'thb-figure-eirin'
    miss_sound_effect = u'thb-cv-eirin_miss'

    notes = u'|RKOF不平衡角色|r'
