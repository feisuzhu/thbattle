# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.cards.classes import AttackCard
from thb.meta.common import ui_meta, N


# -- code --


@ui_meta(characters.sakuya.Sakuya)
class Sakuya:
    # Character
    name        = '十六夜咲夜'
    title       = '完全潇洒的PAD长'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-sakuya'
    figure_image      = 'thb-figure-sakuya'
    miss_sound_effect = 'thb-cv-sakuya_miss'


@ui_meta(characters.sakuya.Dagger)
class Dagger:
    # Skill
    name = '飞刀'
    description = '你可以将一张装备牌当<style=Card.Name>弹幕</style>使用或打出，以此法使用的<style=Card.Name>弹幕</style>无距离限制。'

    def clickable(self):
        me = self.me

        if not (me.cards or me.showncards or me.equips): return False
        return self.accept_cards([characters.sakuya.Dagger(me)])

    def is_complete(self, skill):
        assert skill.is_card(characters.sakuya.Dagger)
        cl = skill.associated_cards
        if len(cl) != 1 or 'equipment' not in cl[0].category:
            return (False, '请选择一张装备牌！')
        return (True, '快看！灰出去了！')

    def is_action_valid(self, sk, tl):
        rst, reason = self.is_complete(sk)
        if not rst:
            return rst, reason
        else:
            return AttackCard().ui_meta.is_action_valid(sk, tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        src, tgt = act.source, act.target
        sk = act.card
        c = sk.associated_cards[0]
        return f'{N.char(src)}将{N.card(c)}制成了<style=Skill.Name>飞刀</style>，向{N.char(tgt)}掷去！'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-sakuya_dagger1',
            'thb-cv-sakuya_dagger2',
        ])


@ui_meta(characters.sakuya.LunaDialActionStage)
class LunaDialActionStage:
    def sound_effect(self, act):
        return 'thb-cv-sakuya_lunadial'


@ui_meta(characters.sakuya.LunaDial)
class LunaDial:
    # Skill
    name = '月时计'
    description = '<style=B>锁定技</style>，准备阶段开始时，你执行一个额外的出牌阶段。'
