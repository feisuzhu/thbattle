# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import actions, characters
from thb.cards.base import Card
from thb.cards.classes import ExinwanCard, RejectCard
from thb.meta.common import card_desc, limit1_skill_used, passive_clickable, passive_is_action_valid
from thb.meta.common import ui_meta


# -- code --


@ui_meta(characters.reimu.Flight)
class Flight:
    # Skill
    name = '飞行'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.reimu.SpiritualAttack)
class SpiritualAttack:
    name = '灵击'

    def clickable(self, g):
        me = g.me

        if not (me.cards or me.showncards): return False

        try:
            act = g.hybrid_stack[-1]
            if act.cond([characters.reimu.SpiritualAttack(me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(self, g, skill):
        me = g.me
        assert skill.is_card(characters.reimu.SpiritualAttack)
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, '请选择1张手牌！')

        c = acards[0]

        if c.resides_in not in (me.cards, me.showncards):
            return (False, '只能使用手牌发动！')
        elif not c.color == Card.RED:
            return (False, '请选择红色手牌！')

        return (True, '反正这条也看不到，偷个懒~~~')

    def is_action_valid(self, g, cl, tl):
        return (False, '你不能主动使用灵击')

    def sound_effect(self, act):
        return 'thb-cv-reimu_sa'

    def effect_string(self, act):
        return RejectCard.ui_meta.effect_string(act)


@ui_meta(characters.reimu.TributeTarget)
class TributeTarget:
    # Skill
    name = '纳奉'
    description = '|BBOSS技|r，其他角色的出牌阶段限一次，若你的手牌数小于体力上限，其可以将一张手牌置入你的明牌区。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.reimu.Tribute)
class Tribute:
    # Skill
    name = '赛钱'
    description = '出牌阶段限一次，若灵梦的手牌数小于体力上限，你可以将一张手牌置入灵梦的明牌区。'

    def clickable(self, game):
        me = game.me

        if limit1_skill_used('tribute_tag'):
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(self, g, cl, tl):
        cl = cl[0].associated_cards
        if not cl: return (False, '请选择要给出的牌')
        if len(cl) != 1: return (False, '只能选择一张手牌')

        if not cl[0].resides_in.type in ('cards', 'showncards'):
            return (False, '只能选择手牌！')

        if len(tl) != 1 or not tl[0].has_skill(characters.reimu.TributeTarget):
            return (False, '请选择一只灵梦')

        if len(tl[0].cards) + len(tl[0].showncards) >= tl[0].maxlife:
            return (False, '灵梦的赛钱箱满了')

        return (True, '投进去……会发生什么呢？')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return (
            '|G【%s】|r向|G【%s】|r的赛钱箱里放了一张%s… 会发生什么呢？'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card.associated_cards[0]),
        )

    def sound_effect(self, act):
        c = act.card.associated_cards[0]
        if c.is_card(ExinwanCard):
            return 'thb-cv-reimu_tribute_exinwan'
        else:
            return random.choice([
                'thb-cv-reimu_tribute1',
                'thb-cv-reimu_tribute2',
            ])


# ----------------------

@ui_meta(characters.reimu.ReimuExterminate)
class ReimuExterminate:
    # Skill
    name = '退治'
    description = (
        '其他角色的回合内，你可以于以下时机无视距离对其使用一张弹幕：\n'
        '|B|R>> |r出牌阶段，你受到伤害后\n'
        '|B|R>> |r回合结束阶段，且该角色本回合对其他角色造成过伤害'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.reimu.ReimuExterminateAction)
class ReimuExterminateAction:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '代表幻想乡消灭你！')
        else:
            return (False, '退治：选择一张弹幕对%s使用（否则不发动）' % act.victim.ui_meta.name)


@ui_meta(characters.reimu.ReimuExterminateLaunchCard)
class ReimuExterminateLaunchCard:
    def effect_string_before(self, act):
        if act.cause == 'damage':
            return '|G【%s】|r： (╯‵□′)╯︵ ┻━┻ ！！！' % act.source.ui_meta.name
        else:
            return '听说异变的元凶是|G【%s】|r，|G【%s】|r马上就出现了！' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
            )

    def sound_effect(self, act):
        if act.cause == 'damage':
            return 'thb-cv-reimu_exterminate_damage'
        else:
            return 'thb-cv-reimu_exterminate_active'


@ui_meta(characters.reimu.ReimuClear)
class ReimuClear:
    # Skill
    name = '快晴'
    description = '你对一名其他角色造成伤害后，你可以与其各摸一张牌，若此时位于其它角色的出牌阶段，停止当前结算并结束出牌阶段。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.reimu.ReimuClearAction)
class ReimuClearAction:
    def effect_string_before(self, act):
        return '异变解决啦！|G【%s】|r和|G【%s】|r一起去吃饭了！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-reimu_clear'


@ui_meta(characters.reimu.ReimuClearHandler)
class ReimuClearHandler:
    choose_option_prompt  = '要发动【快晴】吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(characters.reimu.Reimu)
class Reimu:
    # Character
    name        = '博丽灵梦'
    title       = '节操满地跑的城管'
    illustrator = '和茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-reimu'
    figure_image      = 'thb-figure-reimu'
    miss_sound_effect = 'thb-cv-reimu_miss'
