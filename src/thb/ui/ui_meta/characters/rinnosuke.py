# -*- coding: utf-8 -*-

# -- stdlib --
import time

# -- third party --
# -- own --
from thb import actions, characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.rinnosuke)


class Netoru:
    # Skill
    name = u'寝取'
    description = u'出牌阶段限一次，你可以弃置两张手牌并指定一名已受伤的其他角色，你与其各回复1点体力。'

    def clickable(game):
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

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        me = g.me
        if not cl or len(cl) != 2:
            return (False, u'请选择两张手牌')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, u'只能使用手牌发动！')

        if len(tl) != 1:
            return (False, u'请选择一名受伤的玩家')

        t = tl[0]
        if t.life >= t.maxlife:
            return (False, u'这位少女节操满满，不会答应你的…')
        else:
            return (True, u'少女，做个好梦~')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r一改平日的猥琐形象，竟然用花言巧语将|G【%s】|r骗去啪啪啪了！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-rinnosuke_nitoru'


class Psychopath:
    # Skill
    name = u'变态'
    description = u'|B锁定技|r，当你失去一张装备区里的牌时，你摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class PsychopathDrawCards:
    def effect_string(act):
        return (
            u'|G【%s】|r满脸猥琐地将装备脱掉，结果众人抄起了%d张牌糊在了他身上。'
        ) % (
            act.target.ui_meta.name,
            act.amount,
        )

    def sound_effect(act):
        tgt = act.target
        t = tgt.tags
        if time.time() - t['__psycopath_lastplay'] > 10:
            t['__psycopath_lastplay'] = time.time()
            return 'thb-cv-rinnosuke_psycopath'


class Rinnosuke:
    # Character
    name        = u'森近霖之助'
    title       = u'变态出没注意'
    illustrator = u'Pixiv ID 1666615'
    cv          = u'大白'

    port_image        = u'thb-portrait-rinnosuke'
    figure_image      = u''
    miss_sound_effect = u'thb-cv-rinnosuke_miss'
