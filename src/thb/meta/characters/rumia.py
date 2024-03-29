# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, N

# -- code --


@ui_meta(characters.rumia.Darkness)
class Darkness:
    # Skill
    name = '黑暗'
    description = (
        '出牌阶段限一次，你可以弃置一张牌并指定一名其他角色，令其选择一项：'
        '<style=Desc.Li>对其攻击范围内另一名你指定的其他角色使用一张<style=Card.Name>弹幕</style>。</style>'
        '<style=Desc.Li>受到你造成的1点伤害。</style>'
    )

    custom_ray = True

    def clickable(self):
        g = self.game
        try:
            if self.limit1_skill_used('darkness_tag'):
                return False
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(self, sk, tl):
        cl = sk.associated_cards
        if not cl or len(cl) != 1:
            return (False, '请选择一张牌')

        if not len(tl):
            return (False, '请选择第一名玩家（向第二名玩家出<style=Card.Name>弹幕</style>）')
        elif len(tl) == 1:
            return (False, '请选择第二名玩家（<style=Card.Name>弹幕</style>的目标）')
        else:
            return (True, '你们的关系…是~这样吗？')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        a, b, *_ = act.target_list
        return f'{N.char(src)}在黑暗中一通乱搅，结果{N.char(a)}和{N.char(b)}打了起来！'

    def sound_effect(self, act):
        return 'thb-cv-rumia_darkness'


@ui_meta(characters.rumia.DarknessKOF)
class DarknessKOF:
    # Skill
    name = '黑暗'
    description = '<style=B>登场技</style>，你登场的回合，对方使用牌时不能指定你为目标。'


@ui_meta(characters.rumia.DarknessKOFAction)
class DarknessKOFAction:

    def effect_string(self, act):
        return f'{N.char(act.source)}一出现天就黑了，低头都看不见胖次！'

    def sound_effect(self, act):
        return 'thb-cv-rumia_darkness_kof'


@ui_meta(characters.rumia.DarknessKOFLimit)
class DarknessKOFLimit:
    shootdown_message = '<style=Skill.Name>黑暗</style>：你不能对其使用卡牌'


@ui_meta(characters.rumia.DarknessAction)
class DarknessAction:
    def ray(self, act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]

    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '使用<style=Card.Name>弹幕</style>')
        else:
            return (False, '请使用一张<style=Card.Name>弹幕</style>（否则受到一点伤害）')


@ui_meta(characters.rumia.Cheating)
class Cheating:
    # Skill
    name = '作弊'
    description = '<style=B>锁定技</style>，结束阶段开始时，你摸一张牌。'


@ui_meta(characters.rumia.CheatingDrawCards)
class CheatingDrawCards:
    def effect_string(self, act):
        return '突然不知道是谁把太阳挡住了。等到大家回过神来，赫然发现牌堆里少了一张牌！'

    def sound_effect(self, act):
        return 'thb-cv-rumia_cheat'


@ui_meta(characters.rumia.Rumia)
class Rumia:
    # Character
    name        = '露米娅'
    title       = '宵暗的妖怪'
    illustrator = '和茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-rumia'
    figure_image      = 'thb-figure-rumia'
    miss_sound_effect = 'thb-cv-rumia_miss'


@ui_meta(characters.rumia.RumiaKOF)
class RumiaKOF:
    # Character
    name        = '露米娅'
    title       = '宵暗的妖怪'
    illustrator = '和茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-rumia'
    figure_image      = 'thb-figure-rumia'
    miss_sound_effect = 'thb-cv-rumia_miss'

    notes = 'KOF修正角色'
