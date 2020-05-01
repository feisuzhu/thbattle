# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.suwako)


class Divine:
    # Skill
    name = u'神御'
    description = u'准备阶段开始时，你可以获得一名与你距离2以内角色的一张手牌；若如此做，你的弃牌阶段结束后，该角色从你的弃牌中获得一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DivineFetchHandler:
    def target(pl):
        if not pl:
            return (False, u'神御：请选择1名玩家（可取消）')

        return (True, u'神御：获得该角色的1张手牌')


class DivineFetchAction:
    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G神御|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return ''


class DivinePickAction:
    # string to modify: it can work and it shall include name of target (possessing Divine)
    def effect_string(act):
        c = getattr(act, 'card', None)
        src = act.source
        if c:
            return u'（神御效果补偿）|G【%s】|r获得了|G%s|r。' % (
            src.ui_meta.name,
            card_desc(c),
        )

    def sound_effect(act):
        return ''


class SpringSign:
    # Skill
    name = u'丰源'
    description = u'|B锁定技|r，​你的出牌阶段结束时，你摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SpringSignDrawCards:
    def effect_string(act):
        # needed > _ <
        return u'（丰源效果台词）'

    def sound_effect(act):
        return ''


class Suwako:
    # Character
    name        = u'洩矢诹访子'
    title       = u'土谷神之假身'
    illustrator = u'暂缺'
    cv          = u'暂缺'

    port_image        = u'thb-portrait-suwako'
    figure_image      = u''
    miss_sound_effect = u''
