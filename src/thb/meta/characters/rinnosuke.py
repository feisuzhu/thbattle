# -*- coding: utf-8 -*-

# -- stdlib --
import time

# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


class Netoru:
    # Skill
    name = '寝取'
    description = '出牌阶段限一次，你可以弃置两张手牌并指定一名已受伤的其他角色，你与其各回复1点体力'

    def clickable(self, game):
        me = game.me
        try:
            if me.tags['netoru_tag'] >= me.tags['turn_count']:
                return False
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        me = g.me
        if not cl or len(cl) != 2:
            return (False, '请选择两张手牌')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, '只能使用手牌发动！')

        if len(tl) != 1:
            return (False, '请选择一名受伤的玩家')

        t = tl[0]
        if t.life >= t.maxlife:
            return (False, '这位少女节操满满，不会答应你的…')
        else:
            return (True, '少女，做个好梦~')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return '|G【%s】|r一改平日的猥琐形象，竟然用花言巧语将|G【%s】|r骗去啪啪啪了！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-rinnosuke_nitoru'


@ui_meta(characters.rinnosuke.Psychopath)
class Psychopath:
    # Skill
    name = '变态'
    description = '|B锁定技|r，当你失去一张装备区里的装备牌时，你摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.rinnosuke.PsychopathDrawCards)
class PsychopathDrawCards:
    def effect_string(self, act):
        return (
            '|G【%s】|r满脸猥琐地将装备脱掉，结果众人抄起了%d张牌糊在了他身上。'
        ) % (
            act.target.ui_meta.name,
            act.amount,
        )

    def sound_effect(self, act):
        tgt = act.target
        t = tgt.tags
        if time.time() - t['__psycopath_lastplay'] > 10:
            t['__psycopath_lastplay'] = time.time()
            return 'thb-cv-rinnosuke_psycopath'


@ui_meta(characters.rinnosuke.Rinnosuke)
class Rinnosuke:
    # Character
    name        = '森近霖之助'
    title       = '变态出没注意'
    illustrator = '霏茶'
    cv          = '大白'

    port_image        = 'thb-portrait-rinnosuke'
    # figure_image      = u'thb-figure-rinnosuke'
    figure_image      = ''
    miss_sound_effect = 'thb-cv-rinnosuke_miss'
