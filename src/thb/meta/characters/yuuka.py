# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.classes import AttackCard
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.yuuka.ReversedScales)
class ReversedScales:
    # Skill
    name = '逆鳞'
    description = '每当你成为其他角色使用的单体符卡效果目标时，你可以将其视为<style=Card.Name>弹幕战</style>效果；你的回合外，你可以将一张手牌当做<style=Card.Name>弹幕</style>使用或打出。'

    def clickable(self):
        me = self.me
        if self.my_turn():
            return False

        if not (me.cards or me.showncards):
            return False

        return self.accept_cards([self.build_handcard(AttackCard)])

    def is_complete(self, skill):
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, '请选择1张牌！')

        return (True, '反正这条也看不到，偷个懒~~~')

    def is_action_valid(self, sk, tl):
        rst, reason = self.is_complete(sk)
        if not rst:
            return (rst, reason)
        else:
            return AttackCard().ui_meta.is_action_valid([sk], tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'{N.char(act.source)}给了{N.char(act.target)}一个和善的眼神。'

    def sound_effect(self, act):
        return 'thb-cv-yuuka_flowerqueen'


@ui_meta(characters.yuuka.Sadist)
class Sadist:
    # Skill
    name = '施虐'
    description = '当你击坠一名角色时，你可以对攻击范围内一名其他角色造成1点伤害；你对体力值为1的其他角色造成的伤害+1。'


@ui_meta(characters.yuuka.SadistKOF)
class SadistKOF:
    # Skill
    name = '施虐'
    description = '<style=B>锁定技</style>，当你击坠对手后，你摸2张牌并对其下一名登场角色造成1点伤害。'


@ui_meta(characters.yuuka.ReversedScalesAction)
class ReversedScalesAction:
    def effect_string_apply(self, act):
        return f'{N.char(act.target)}：“来正面上我啊！”'

    def sound_effect(self, act):
        return 'thb-cv-yuuka_rs'


@ui_meta(characters.yuuka.SadistAction)
class SadistAction:
    def effect_string_apply(self, act):
        return f'{N.char(act.source)}又看了看{N.char(act.target)}：“你也要尝试一下么！”'

    def sound_effect(self, act):
        return 'thb-cv-yuuka_sadist'


@ui_meta(characters.yuuka.SadistKOFDamageAction)
class SadistKOFDamageAction:
    def effect_string_apply(self, act):
        return f'{N.char(act.source)}又看了看{N.char(act.target)}：“你也要尝试一下么！”'

    def sound_effect(self, act):
        return 'thb-cv-yuuka_sadist'


@ui_meta(characters.yuuka.SadistHandler)
class SadistHandler:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '发动<style=Skill.Name>施虐</style>')
        else:
            return (False, '<style=Skill.Name>施虐</style>：请弃置一张牌')

    def target(self, pl):
        if not pl:
            return (False, '<style=Skill.Name>施虐</style>：请选择1名玩家')

        return (True, '发动<style=Skill.Name>施虐</style>')


@ui_meta(characters.yuuka.ReversedScalesHandler)
class ReversedScalesHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>逆鳞</style>吗？'


@ui_meta(characters.yuuka.Yuuka)
class Yuuka:
    # Character
    name        = '风见幽香'
    title       = '四季的鲜花之主'
    illustrator = '霏茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-yuuka'
    figure_image      = 'thb-figure-yuuka'
    miss_sound_effect = 'thb-cv-yuuka_miss'


@ui_meta(characters.yuuka.YuukaKOF)
class YuukaKOF:
    # Character
    name        = '风见幽香'
    title       = '四季的鲜花之主'
    illustrator = '霏茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-yuuka'
    figure_image      = 'thb-figure-yuuka'
    miss_sound_effect = 'thb-cv-yuuka_miss'

    notes = 'KOF修正角色'
