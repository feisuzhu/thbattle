# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn
from thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.minoriko)


class Foison:
    # Skill
    name = u'丰收'
    description = u'|B锁定技|r，摸牌阶段摸牌后，你将手牌数补至五张。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FoisonDrawCardStage:
    def effect_string(act):
        return u'大丰收！|G【%s】|r一下子收获了%d张牌！' % (
            act.source.ui_meta.name,
            act.amount,
        )

    def sound_effect(act):
        return 'thb-cv-minoriko_foison'


class AutumnFeast:
    # Skill
    name = u'秋祭'
    description = u'出牌阶段限一次，你可以将两张红色牌当|G五谷丰登|r使用。'

    def clickable(game):
        me = game.me
        if not my_turn(): return False
        if limit1_skill_used('autumnfeast_tag'): return False

        if not (me.cards or me.showncards or me.equips):
            return False

        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        from thb.cards import Card
        if len(cl) != 2 or any(c.color != Card.RED for c in cl):
            return (False, u'请选择2张红色的牌！')
        return (True, u'发麻薯啦~')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        return (
            u'|G【%s】|r：麻薯年年有，今年特别多！'
        ) % (
            source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-minoriko_autumnfeast'


class AkiTribute:
    # Skill
    name = u'上贡'
    description = u'|B锁定技|r，结算|G五谷丰登|r时，你首先选择牌，结算完后，你将剩余的牌置于一名角色的明牌区。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AkiTributeCollectCard:
    def sound_effect(act):
        return 'thb-cv-minoriko_akitribute'


class AkiTributeHandler:

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家，将剩余的牌置入该玩家的明牌区')

        return (True, u'浪费粮食，可不是好行为！')


class Minoriko:
    # Character
    name        = u'秋穰子'
    title       = u'没人气的丰收神'
    illustrator = u'和茶'
    cv          = u'VV'

    port_image        = u'thb-portrait-minoriko'
    figure_image      = u'thb-figure-minoriko'
    miss_sound_effect = u'thb-cv-minoriko_miss'
