# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import actions, characters
from thb.actions import PlayerTurn, ttags
from thb.cards.classes import AttackCard, GrazeCard
from thb.meta.common import ui_meta


# -- code --
@ui_meta(characters.nitori.Dismantle)
class Dismantle:
    # Skill
    name = '拆解'
    description = '出牌阶段限一次，你可以|B重铸|r一名其他角色装备区里的一张装备牌，然后该角色摸一张牌。'

    def clickable(self):
        if ttags(self.me)['dismantle']:
            return False

        return self.my_turn()

    def is_action_valid(self, sk, tl):
        if sk.associated_cards:
            return (False, '请不要选择牌！')

        if not len(tl):
            return (False, '请选择一名玩家')

        return (True, '拆解！')

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-nitori_dismantle',
            'thb-cv-nitori_dismantle_other',
        ])


@ui_meta(characters.nitori.Craftsman)
class Craftsman:
    name = '匠心'
    description = '你可以将你的全部手牌（至少1张）当做任意的一张基本牌使用或打出。出牌阶段内使用时，一回合限一次。'

    params_ui = 'UICraftsmanCardSelection'

    def clickable(self, g):
        try:
            me = g.me
            if not me.cards and not me.showncards:
                return False

            current = PlayerTurn.get_current(g).target
            if ttags(me)['craftsman'] and current is me:
                return False

            return True

        except (IndexError, AttributeError):
            return False

    def is_complete(self, skill):
        me = self.me
        assert skill.is_card(characters.nitori.Craftsman)
        if set(skill.associated_cards) != set(me.cards) | set(me.showncards):
            return (False, '请选择所有的手牌（包括明牌）！')

        return (True, '我TMD有老婆了！')

    def is_action_valid(self, sk, tl):
        assert sk.is_card(characters.nitori.Craftsman)
        rst, reason = self.is_complete(sk)
        if not rst:
            return (rst, reason)
        else:
            return sk.treat_as.ui_meta.is_action_valid([sk], tl)

    def effect_string(self, act):
        # for LaunchCard.effect_string
        source = act.source
        s = '|G【%s】|r发动了|G匠心|r。' % (
            source.ui_meta.name,
        )
        return s

    def sound_effect(self, act):
        if isinstance(act, actions.LaunchCard):
            if act.card.is_card(AttackCard):
                l = ['1', '2']
            else:
                l = ['_graze']

        elif isinstance(act, actions.AskForCard):
            atk = act.cond([self.build_handcard(AttackCard, act.target)])
            graze = act.cond([self.build_handcard(GrazeCard, act.target)])
            if atk and not graze:
                l = ['1', '2']
            else:
                l = ['_graze']
        else:
            l = []

        return l and 'thb-cv-nitori_craftsman%s' % random.choice(l)


@ui_meta(characters.nitori.Nitori)
class Nitori:
    # Character
    name        = '河城荷取'
    title       = '水中的工程师'
    illustrator = '和茶'
    cv          = '简翎'

    port_image        = 'thb-portrait-nitori'
    figure_image      = 'thb-figure-nitori'
    miss_sound_effect = ''

    notes = '|RKOF不平衡角色|r'
