# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.keine.Teach)
class Teach:
    # Skill
    name = '授业'
    description = (
        '出牌阶段限一次，你可以重铸一张牌，然后将一张牌交给一名其它角色，其选择一项：'
        '<style=Desc.Li>使用一张牌，</style><style=Desc.Li>重铸一张牌。</style>'
    )

    def clickable(self):
        return self.my_turn() and not ttags(self.me)['teach_used']

    def is_action_valid(self, sk, tl):
        cards = sk.associated_cards

        if not cards or len(cards) != 1:
            return False, '请选择一张牌（重铸）'

        if not tl or len(tl) != 1:
            return False, '请选择一个目标'

        return True, '发动<style=Skill.Name>授业</style>'

    def effect_string(self, act):
        return f'“是这样的{N.char(act.target)}”，{N.char(act.source)}说道，“两个1相加是不等于⑨的。即使是两个⑥也不行。不不，天才来算也不行。”'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-keine_teach1',
            'thb-cv-keine_teach2',
        ])


@ui_meta(characters.keine.TeachAction)
class TeachAction:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '给出这张牌')
        else:
            return (False, '请选择你要给出的牌')

    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '传道授业！')


@ui_meta(characters.keine.TeachTargetEffect)
class TeachTargetEffect:
    # choose_option
    choose_option_buttons = (('重铸一张牌', 'reforge'), ('使用卡牌', 'action'))
    choose_option_prompt = '<style=Skill.Name>授业</style>：请选择你的行动'


@ui_meta(characters.keine.TeachTargetReforgeAction)
class TeachTargetReforgeAction:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '重铸这张牌')
        else:
            return (False, '请选择一张牌重铸')

    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '传道授业！')


@ui_meta(characters.keine.KeineGuard)
class KeineGuard:
    # Skill
    name = '守护'
    description = (
        '<style=B>限定技</style>，出牌阶段开始时，你可以失去一点体力上限，令一名其它已受伤角色回复一点体力。之后，若其体力仍然是全场最低的，则你与其获得技能<style=Skill.Name>决意</style>。'
        '<style=Desc.Li><style=Skill.Name>决意</style>：当你受到伤害时，若同样拥有<style=Skill.Name>决意</style>的另一名角色的体力值比你高，则伤害改为由该角色承受。同样拥有<style=Skill.Name>决意</style>的另一名角色于你的回合内摸牌/回复体力时，你摸相同数量的牌/回复相同的体力。</style>'
    )

    def is_available(self, ch):
        return characters.keine.KeineGuard in ch.skills


@ui_meta(characters.keine.KeineGuardAction)
class KeineGuardAction:
    def effect_string_before(self, act):
        return f'“我绝对不会让你们碰到{N.char(act.target)} 一根手指的！”{N.char(act.source)}冲着所有人喊道。'

    def sound_effect_before(self, act):
        return random.choice([
            'thb-cv-keine_guard_awake',
        ])


@ui_meta(characters.keine.KeineGuardHandler)
class KeineGuardHandler:

    def target(self, pl):
        if not pl:
            return (False, u'<style=Skill.Name>守护</style>：请选择1名其他角色（或不发动）')

        p = pl[0]
        if p.life >= p.maxlife:
            return False, u'目标角色没有受伤'

        return True, u'我的CP由我来守护！'


@ui_meta(characters.keine.Devoted)
class Devoted:
    # Skill
    name = u'决意'
    description = (
        '当你受到伤害时，若同样拥有<style=Skill.Name>决意</style>的另一名角色的体力值比你高，则伤害改为由该角色承受。同样拥有<style=Skill.Name>决意</style>的另一名角色于你的回合内摸牌/回复体力时，你摸相同数量的牌/回复相同的体力。'
    )


@ui_meta(characters.keine.DevotedHeal)
class DevotedHeal:
    def effect_string(self, act):
        return f'{N.char(act.source)}分享了回复效果（<style=Skill.Name>决意</style>），{N.char(act.target)}回复了{act.amount}点体力。'


@ui_meta(characters.keine.DevotedDrawCards)
class DevotedDrawCards:
    def effect_string(self, act):
        return f'{N.char(act.source)}分享了摸牌效果（<style=Skill.Name>决意</style>），{N.char(act.target)}摸了{act.amount}张牌。'


@ui_meta(characters.keine.DevotedAction)
class DevotedAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}的伤害由{N.char(act.target)}承受了（<style=Skill.Name>决意</style>）。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(characters.keine.Keine)
class Keine:
    # Character
    name        = '上白泽慧音'
    title       = '人间之里的守护者'
    illustrator = '和茶'
    cv          = '银子'

    port_image        = 'thb-portrait-keine'
    figure_image      = 'thb-figure-keine'
    miss_sound_effect = 'thb-cv-keine_miss'

    notes = 'KOF不平衡角色'
