# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.cards.base import Card, VirtualCard
from thb.meta.common import passive_clickable, passive_is_action_valid, ui_meta

# -- code --


@ui_meta(characters.kogasa.Jolly)
class Jolly:
    # Skill
    name = '愉快'
    description = '|B锁定技|r，摸牌阶段摸牌后，你令一名角色摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.kogasa.JollyDrawCard)
class JollyDrawCard:
    def effect_string(self, act):
        return '|G【%s】|r高兴地让|G【%s】|r摸了%d张牌~' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            act.amount,
        )

    def sound_effect(self, act):
        return 'thb-cv-kogasa_jolly'


@ui_meta(characters.kogasa.JollyHandler)
class JollyHandler:
    def choose_card_text(self, g, act, cards):
        if cards:
            return (False, '请不要选择牌！')

        return (True, '(～￣▽￣)～')

    # choose_players
    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家，该玩家摸一张牌')

        return (True, '(～￣▽￣)～')


@ui_meta(characters.kogasa.Surprise)
class Surprise:
    # Skill
    name = '惊吓'
    description = '出牌阶段限一次，你可以选择一张手牌并指定一名其他角色，该角色选择一种花色后，获得此牌并明置之。若此牌与其选择的花色不同，你对其造成1点伤害。'

    def clickable(self, game):
        me = game.me

        if me.tags.get('surprise_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards):
            return True

        return False

    def is_action_valid(self, g, cl, tl):
        if len(tl) != 1:
            return (False, '请选择惊吓对象…')

        cl = cl[0].associated_cards
        if len(cl) != 1:
            return (False, '请选择一张手牌！')

        c, = cl
        if c.is_card(VirtualCard) or c.resides_in.type not in ('cards', 'showncards'):
            return (False, '请选择一张手牌！')

        # return (True, u'(´・ω・`)')
        return (True, '\ ( °▽ °) /')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return (
            '|G【%s】|r突然出现在|G【%s】|r面前，伞上'
            '的大舌头直接糊在了|G【%s】|r的脸上！'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-kogasa_surprise'


@ui_meta(characters.kogasa.SurpriseAction)
class SurpriseAction:
    # choose_option
    choose_option_buttons = (
        ('黑桃', Card.SPADE),
        ('红桃', Card.HEART),
        ('草花', Card.CLUB),
        ('方片', Card.DIAMOND),
    )

    # choose_option
    choose_option_buttons = (
        ('♠', Card.SPADE),
        ('♥', Card.HEART),
        ('♣', Card.CLUB),
        ('♦', Card.DIAMOND),
    )

    choose_option_prompt = '请选择一个花色…'

    def effect_string(self, act):
        if act.succeeded:
            return '效果拔群！'
        else:
            return '似乎没有什么效果'


@ui_meta(characters.kogasa.Kogasa)
class Kogasa:
    # Character
    name        = '多多良小伞'
    title       = '愉快的遗忘之伞'
    illustrator = '霏茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-kogasa'
    figure_image      = 'thb-figure-kogasa'
    miss_sound_effect = 'thb-cv-kogasa_miss'
