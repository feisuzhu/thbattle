# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --

# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.rinnosuke.Netoru)
class Netoru:
    # Skill
    name = '午茶'
    description = '出牌阶段限一次，你可以弃置两张手牌并指定一名已受伤的其他角色，你与其各回复1点体力。'

    def clickable(self):
        g = self.game
        me = self.me
        try:
            if me.tags['netoru_tag'] >= me.tags['turn_count']:
                return False
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(self, sk, tl):
        cl = sk.associated_cards
        me = self.me
        if not cl or len(cl) != 2:
            return (False, '请选择两张手牌')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, '只能使用手牌发动！')

        if len(tl) != 1:
            return (False, '请选择一名受伤的玩家')

        t = tl[0]
        if t.life >= t.maxlife:
            return (False, '少女吃饱了…')
        else:
            return (True, '下午茶时间到了~')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'{N.char(act.source)}拖着疲惫的{N.char(act.target)}去吃下午茶。真是满足呢。'

    # def sound_effect(self, act):
    #     return 'thb-cv-rinnosuke_nitoru'


@ui_meta(characters.rinnosuke.Psychopath)
class Psychopath:
    # Skill
    name = '鉴宝'
    description = '<style=B>锁定技</style>，当你失去一张装备区里的装备牌时，你摸两张牌。'


@ui_meta(characters.rinnosuke.PsychopathDrawCards)
class PsychopathDrawCards:
    def effect_string(self, act):
        return f'{N.char(act.target)}又脱手了一件宝物，赚到了{act.amount}张牌。'

    # def sound_effect(self, act):
    #     tgt = act.target
    #     t = tgt.tags
    #     if time.time() - t['__psycopath_lastplay'] > 10:
    #         t['__psycopath_lastplay'] = time.time()
    #         return 'thb-cv-rinnosuke_psycopath'


@ui_meta(characters.rinnosuke.Rinnosuke)
class Rinnosuke:
    # Character
    name        = '森近霖之助'
    title       = '变态出没注意'
    illustrator = '霏茶'
    cv          = '大白'

    port_image        = 'thb-portrait-rinnosuke'
    figure_image      = 'thb-figure-rinnosuke'
    # miss_sound_effect = 'thb-cv-rinnosuke_miss'
