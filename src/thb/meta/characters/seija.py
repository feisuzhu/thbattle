# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.seija.InciteAttack)
class InciteAttack:
    name = '挑拨'

    def effect_string(self, act):
        return f'{N.char(act.source)}立刻将<style=Card.Name>弹幕</style>甩在了{N.char(act.source)}的脸上：“看也就看了，能别说么？”'


@ui_meta(characters.seija.InciteFailAttack)
class InciteFailAttack:
    name = '挑拨'

    def effect_string(self, act):
        return f'{N.char(act.source)}立刻将<style=Card.Name>弹幕</style>甩在了{N.char(act.target)}的脸上：“你怎么知道是蓝白条的？”'


@ui_meta(characters.seija.InciteSilentFailAction)
class InciteSilentFailAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}低头看了一眼，诶，好像真的是蓝白条……'


@ui_meta(characters.seija.Incite)
class Incite:
    # Skill
    name = '挑拨'
    description = '出牌阶段限一次，你可以与一名其他角色拼点，若你赢，视为该角色对其攻击范围内你指定的另一名其他角色使用了一张<style=Card.Name>弹幕</style>；若你没赢，该角色可以视为对你使用了一张<style=Card.Name>弹幕</style>。'

    custom_ray = True

    def clickable(self):
        if self.limit1_skill_used('incite_tag'):
            return False

        return self.my_turn()

    def is_action_valid(self, sk, tl):
        if sk.associated_cards:
            return (False, '请不要选择牌！')

        if not len(tl):
            return (False, '请选择第一名玩家（<style=Skill.Name>拼点</style>的对象）')
        elif len(tl) == 1:
            return (False, '请选择第二名玩家（<style=Card.Name>弹幕</style>的目标）')
        else:
            return (True, '大嘴正邪愉快的一天开始了～')

    def effect_string(self, act):
        src = act.source
        tgt, victim = act.target_list
        if victim is src:
            return f'{N.char(src)}一脸坏笑，对{N.char(tgt)}说：“那个啥…… 蓝白条，赞！”'
        else:
            return f'{N.char(src)}一脸坏笑，对{N.char(tgt)}说：“你知道吗，{N.char(victim)}刚才看了你的胖次，蓝白条，赞！”'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-seija_incite1',
            'thb-cv-seija_incite2',
        ])


@ui_meta(characters.seija.InciteAction)
class InciteAction:
    # choose_option
    choose_option_buttons = (('使用', True), ('不使用', False))

    def ray(self, act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]

    def choose_option_prompt(self, act):
        return f'你要对{N.char(act.source)}使用<style=Card.Name>弹幕</style>吗？'


@ui_meta(characters.seija.Reversal)
class Reversal:
    # Skill
    name = '逆转'
    description = '当你受到一名其他角色使用的<style=Card.Name>弹幕</style>效果时，你可以摸一张牌，然后若你的手牌数大于其手牌数，取消该<style=Card.Name>弹幕</style>效果，并视为该角色再对你使用一张<style=Card.Name>弹幕战</style>。'


@ui_meta(characters.seija.ReversalDuel)
class ReversalDuel:
    name = '逆转'

    def effect_string(self, act):
        return f'{N.char(act.target)}对{N.char(act.source)}：“你敢打我脸，我就敢打回去！”'

    def sound_effect(self, act):
        return 'thb-cv-seija_reversal'


@ui_meta(characters.seija.ReversalHandler)
class ReversalHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>逆转</style>吗？'


@ui_meta(characters.seija.Seija)
class Seija:
    # Character
    name        = '鬼人正邪'
    title       = '逆袭的天邪鬼'
    illustrator = '霏茶'
    cv          = '北斗夜'

    port_image        = 'thb-portrait-seija'
    figure_image      = 'thb-figure-seija'
    miss_sound_effect = 'thb-cv-seija_miss'

    notes = 'KOF模式不可用'
