# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, my_turn

# -- code --



@ui_meta(characters.koakuma.Koakuma)
class Koakuma:
    # Character
    name        = '小恶魔'
    title       = '图书管理员'
    illustrator = '渚FUN/Takibi'
    cv          = 'VV'

    port_image        = 'thb-portrait-koakuma'
    figure_image      = 'thb-figure-koakuma'
    miss_sound_effect = 'thb-cv-koakuma_miss'


@ui_meta(characters.koakuma.Find)
class Find:
    # Skill
    name = '寻找'
    description = '出牌阶段限一次，你可以弃置至多X张牌，然后摸等量的牌。（X为场上存活角色数）'

    def clickable(self, game):
        me = game.me
        if ttags(me)['find']:
            return False

        if my_turn() and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.koakuma.Find)
        n = len([i for i in g.players if not i.dead])

        if not 0 < len(skill.associated_cards) <= n:
            return (False, '请选择需要换掉的牌（至多%s张）！' % n)

        if not [g.me] == target_list:
            return (False, 'BUG!!')

        return (True, '换掉这些牌')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        s = '|G【%s】|r发动了寻找技能，换掉了%d张牌。' % (
            source.ui_meta.name,
            len(card.associated_cards),
        )
        return s

    def sound_effect(self, act):
        return 'thb-cv-koakuma_find'
