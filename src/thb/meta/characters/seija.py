# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, limit1_skill_used, my_turn, passive_clickable
from thb.meta.common import passive_is_action_valid


# -- code --


@ui_meta(characters.seija.InciteAttack)
class InciteAttack:
    name = '挑拨'

    def effect_string(self, act):
        return '|G【%s】|r立刻将|G弹幕|r甩在了|G【%s】|r的脸上：“看也就看了，能别说么？”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(characters.seija.InciteFailAttack)
class InciteFailAttack:
    name = '挑拨'

    def effect_string(self, act):
        return '|G【%s】|r立刻将|G弹幕|r甩在了|G【%s】|r的脸上：“你怎么知道是蓝白条的？”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(characters.seija.InciteSilentFailAction)
class InciteSilentFailAction:
    def effect_string(self, act):
        return '|G【%s】|r低头看了一眼，诶，好像真的是蓝白条……' % (
            act.target.ui_meta.name,
        )


@ui_meta(characters.seija.Incite)
class Incite:
    # Skill
    name = '挑拨'
    description = '出牌阶段限一次，你可以与一名其他角色拼点，若你赢，视为该角色对其攻击范围内你指定的另一名其他角色使用了一张|G弹幕|r；若你没赢，该角色可以视为对你使用了一张|G弹幕|r。'

    custom_ray = True

    def clickable(self, game):
        if limit1_skill_used('incite_tag'):
            return False

        return my_turn()

    def is_action_valid(self, g, cl, tl):
        if cl[0].associated_cards:
            return (False, '请不要选择牌！')

        if not len(tl):
            return (False, '请选择第一名玩家（【拼点】的对象）')
        elif len(tl) == 1:
            return (False, '请选择第二名玩家（【弹幕】的目标）')
        else:
            return (True, '大嘴正邪愉快的一天开始了～')

    def effect_string(self, act):
        src = act.source
        tgt, victim = act.target_list
        if victim is src:
            return '|G【%s】|r一脸坏笑，对|G【%s】|r说：“那个啥…… 蓝白条，赞！”' % (
                src.ui_meta.name,
                tgt.ui_meta.name,
            )
        else:
            return '|G【%s】|r一脸坏笑，对|G【%s】|r说：“你知道吗，|G【%s】|r刚才看了你的胖次，蓝白条，赞！”' % (
                src.ui_meta.name,
                tgt.ui_meta.name,
                victim.ui_meta.name,
            )

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
        return '你要对【%s】使用【弹幕】吗？' % act.source.ui_meta.name


@ui_meta(characters.seija.Reversal)
class Reversal:
    # Skill
    name = '逆转'
    description = '当你受到一名其他角色使用的|G弹幕|r效果时，你可以摸一张牌，然后若你的手牌数大于其手牌数，你将此|G弹幕|r视为|G弹幕战|r'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.seija.ReversalDuel)
class ReversalDuel:
    name = '逆转'

    def effect_string(self, act):
        return '|G【%s】|r对|G【%s】|r：“你敢打我脸，我就敢打回去！”' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-seija_reversal'


@ui_meta(characters.seija.ReversalHandler)
class ReversalHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【逆转】吗？'


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

    notes = '|RKOF模式不可用|r'
