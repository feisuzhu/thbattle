# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, limit1_skill_used, my_turn
from thb.meta.common import passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.minoriko.Foison)
class Foison:
    # Skill
    name = '丰收'
    description = '|B锁定技|r，摸牌阶段摸牌后，你将手牌数补至五张。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.minoriko.FoisonDrawCardStage)
class FoisonDrawCardStage:
    def effect_string(self, act):
        return '大丰收！|G【%s】|r一下子收获了%d张牌！' % (
            act.source.ui_meta.name,
            act.amount,
        )

    def sound_effect(self, act):
        return 'thb-cv-minoriko_foison'


@ui_meta(characters.minoriko.AutumnFeast)
class AutumnFeast:
    # Skill
    name = '秋祭'
    description = '出牌阶段限一次，你可以将两张红色牌当|G五谷丰登|r使用。'

    def clickable(self, game):
        me = game.me
        if not my_turn(): return False
        if limit1_skill_used('autumnfeast_tag'): return False

        if not (me.cards or me.showncards or me.equips):
            return False

        return True

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        from thb.cards.classes import Card
        if len(cl) != 2 or any(c.color != Card.RED for c in cl):
            return (False, '请选择2张红色的牌！')
        return (True, '发麻薯啦~')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        return (
            '|G【%s】|r：麻薯年年有，今年特别多！'
        ) % (
            source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-minoriko_autumnfeast'


@ui_meta(characters.minoriko.AkiTribute)
class AkiTribute:
    # Skill
    name = '上贡'
    description = '|B锁定技|r，结算|G五谷丰登|r时，你首先选择牌，结算完后，你将剩余的牌置于一名角色的明牌区。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.minoriko.AkiTributeCollectCard)
class AkiTributeCollectCard:
    def sound_effect(self, act):
        return 'thb-cv-minoriko_akitribute'


@ui_meta(characters.minoriko.AkiTributeHandler)
class AkiTributeHandler:

    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家，将剩余的牌置入该玩家的明牌区')

        return (True, '浪费粮食，可不是好行为！')


@ui_meta(characters.minoriko.Minoriko)
class Minoriko:
    # Character
    name        = '秋穰子'
    title       = '没人气的丰收神'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-minoriko'
    figure_image      = 'thb-figure-minoriko'
    miss_sound_effect = 'thb-cv-minoriko_miss'
