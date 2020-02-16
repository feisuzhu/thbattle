# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import actions, characters
from thb.ui.ui_meta.common import gen_metafunc

# -- code --
__metaclass__ = gen_metafunc(characters.yukari)


class SpiritingAway:
    # Skill
    name = u'神隐'
    description = u'出牌阶段限两次，你可以将场上的一张牌暂时移出游戏。你可以观看以此法移出游戏的牌。任何角色被紫暂时移出的牌，会在紫的结束阶段后归还回该角色的手牌中。'

    def clickable(game):
        me = game.me
        if me.tags['spirit_away_tag'] >= 2: return False
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return (False, u'请不要选择牌')

        if not tl:
            return (False, u'请选择一名玩家')

        tgt = tl[0]
        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        if not any(getattr(tgt, i) for i in catnames):
            return (False, u'这货已经没有牌了')

        return (True, u'发动【神隐】')


class SpiritingAwayAction:

    def effect_string(act):
        words = (
            u'17岁就是17岁，后面没有零几个月！',
            u'叫紫妹就对了，紫妈算什么！',
        )
        # return u'|G【{source}】|r：“{word}”（|G{target}|r的{card}不见了）'.format(
        return u'|G【{source}】|r：“{word}”（|G{target}|r的一张牌不见了）'.format(
            source=act.source.ui_meta.name,
            target=act.target.ui_meta.name,
            word=random.choice(words),
            # card=card_desc(act.card),
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-yukari_spiritaway1',
            'thb-cv-yukari_spiritaway2',
        ])


class Yukari:
    # Character
    name        = u'八云紫'
    title       = u'永远17岁'
    illustrator = u'Vivicat@幻想梦斗符'
    cv          = u'VV'

    port_image        = u'thb-portrait-yukari'
    figure_image      = u'thb-figure-yukari'
    miss_sound_effect = u'thb-cv-yukari_miss'
