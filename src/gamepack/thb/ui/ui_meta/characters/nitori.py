# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from gamepack.thb import actions, cards, characters
from gamepack.thb.actions import ttags
from gamepack.thb.ui.ui_meta.common import build_handcard, gen_metafunc, my_turn


# -- code --
__metaclass__ = gen_metafunc(characters.nitori)


class Dismantle:
    # Skill
    name = u'拆解'

    def clickable(g):
        if ttags(g.me)['dismantle']:
            return False

        return my_turn()

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌！')

        if not len(tl):
            return (False, u'请选择一名玩家')

        return (True, u'拆解！')

    def sound_effect(act):
        return random.choice([
            'thb-cv-nitori_dismantle',
            'thb-cv-nitori_dismantle_other',
        ])


class Craftsman:
    name = u'匠心'
    params_ui = 'UICraftsmanCardSelection'

    def clickable(g):
        try:
            me = g.me
            if not me.cards and not me.showncards:
                return False

            if ttags(me)['craftsman'] and g.current_turn is me:
                return False

            return True

        except (IndexError, AttributeError):
            return False

    def is_complete(g, cl):
        skill = cl[0]
        assert skill.is_card(characters.nitori.Craftsman)
        if set(skill.associated_cards) != set(g.me.cards) | set(g.me.showncards):
            return (False, u'请选择所有的手牌（包括明牌）！')

        return (True, u'到今天为止我还没有女朋友……')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        assert skill.is_card(characters.nitori.Craftsman)
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.effect_string
        source = act.source
        s = u'|G【%s】|r发动了|G匠心|r。' % (
            source.ui_meta.char_name,
        )
        return s

    def sound_effect(act):
        if isinstance(act, actions.LaunchCard):
            if act.card.is_card(cards.AttackCard):
                l = ['1', '2']
            else:
                l = ['_graze']

        elif isinstance(act, actions.AskForCard):
            atk = act.cond([build_handcard(cards.AttackCard, act.target)])
            graze = act.cond([build_handcard(cards.GrazeCard, act.target)])
            if atk and not graze:
                l = ['1', '2']
            else:
                l = ['_graze']
        else:
            l = None

        return l and 'thb-cv-nitori_craftsman%s' % random.choice(l)


class Nitori:
    # Character
    char_name = u'河城荷取'
    port_image = 'thb-portrait-nitori'
    description = (
        u'|DB水中的工程师 河城荷取 体力：3|r\n'
        u'\n'
        u'|G拆解|r：出牌阶段限一次，你可以|B重铸|r一名其他角色装备区里的一张装备牌，然后该角色摸一张牌。\n'
        u'\n'
        u'|G匠心|r：你可以将你的全部手牌（至少1张）当做任意的一张基本牌使用或打出。出牌阶段内使用时，一回合限一次。\n'
        u'\n'
        u'|RKOF不平衡角色|r\n'
        u'\n'
        u'|DB（CV：简翎）|r'
    )
