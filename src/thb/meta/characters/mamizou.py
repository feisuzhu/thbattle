# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.mamizou.Morphing)
class Morphing:
    # Skill
    name = '变化'
    description = '出牌阶段限一次，你可以将两张手牌当任意基本牌或非延时符卡使用，这两张牌中至少有一张须与你声明使用的牌类型相同。'

    params_ui = 'UIMorphingCardSelection'

    def clickable(self):
        me = self.me

        if self.limit1_skill_used('mamizou_morphing_tag'):
            return False

        if not (self.my_turn() and (me.cards or me.showncards)):
            return False

        return True

    def is_action_valid(self, sk, tl):
        assert sk.is_card(characters.mamizou.Morphing)
        cl = sk.associated_cards
        if len(cl) != 2 or any([c.resides_in.type not in ('cards', 'showncards') for c in cl]):
            return (False, '请选择两张手牌！')

        cls = sk.get_morph_cls()
        if not cls:
            return (False, '请选择需要变化的牌')

        if not sk.is_morph_valid():
            return (False, '选择的变化牌不符和规则')

        return sk.treat_as().ui_meta.is_action_valid(sk, tl)

    def effect_string(self, act: actions.LaunchCard):
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        sk = act.card
        assert isinstance(sk, characters.mamizou.Morphing)
        tl = act.target_list
        cl = sk.associated_cards
        s = f'{N.char(src)}发动了<style=Skill.Name>变化</style>技能，将{N.card(cl)}当作{N.card(sk.treat_as)}对{N.char(tl)}使用。'

        return s

    def sound_effect(self, act):
        return 'thb-cv-mamizou_morph'

    # ----- FOR UI -----
    def list_morph_cards(self, cls, sid_list):
        g = self.game
        cl = [g.deck.lookup(c) for c in sid_list]
        cl = cls.list_morph_cards(cl)
        from thb.meta import view
        return [view.card(c) for c in cl]


@ui_meta(characters.mamizou.Mamizou)
class Mamizou:
    # Character
    name        = '二岩猯藏'
    title       = '大狸子'
    designer    = '鵺子丶爱丽丝'
    illustrator = 'hacko.@星の妄想乡'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-mamizou'
    figure_image      = 'thb-figure-mamizou'
    miss_sound_effect = 'thb-cv-mamizou_miss'

    notes = 'KOF模式不可用'
