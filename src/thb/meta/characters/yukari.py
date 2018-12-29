# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta

# -- code --


@ui_meta(characters.yukari.SpiritingAway)
class SpiritingAway:
    # Skill
    name = '神隐'
    description = '出牌阶段限两次，你可以将场上的一张牌暂时移出游戏。你可以观看以此法移出游戏的牌。'

    def clickable(self, game):
        me = game.me
        if me.tags['spirit_away_tag'] >= 2: return False
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '请选择一名玩家')

        tgt = tl[0]
        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        if not any(getattr(tgt, i) for i in catnames):
            return (False, '这货已经没有牌了')

        return (True, '发动【神隐】')


@ui_meta(characters.yukari.SpiritingAwayAction)
class SpiritingAwayAction:

    def effect_string(self, act):
        words = (
            '17岁就是17岁，后面没有零几个月！',
            '叫紫妹就对了，紫妈算什么！',
        )
        # return u'|G【{source}】|r：“{word}”（|G{target}|r的{card}不见了）'.format(
        return '|G【{source}】|r：“{word}”（|G{target}|r的一张牌不见了）'.format(
            source=act.source.ui_meta.name,
            target=act.target.ui_meta.name,
            word=random.choice(words),
            # card=card_desc(act.card),
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-yukari_spiritaway1',
            'thb-cv-yukari_spiritaway2',
        ])


@ui_meta(characters.yukari.Yukari)
class Yukari:
    # Character
    name        = '八云紫'
    title       = '永远17岁'
    illustrator = 'Vivicat@幻想梦斗符'
    cv          = 'VV'

    port_image        = 'thb-portrait-yukari'
    figure_image      = 'thb-figure-yukari'
    miss_sound_effect = 'thb-cv-yukari_miss'
