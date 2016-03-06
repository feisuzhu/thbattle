# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, cards, characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.kogasa)


class Jolly:
    # Skill
    name = u'愉快'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class JollyDrawCard:
    def effect_string(act):
        return u'|G【%s】|r高兴地让|G【%s】|r摸了%d张牌~' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.amount,
        )

    def sound_effect(act):
        return 'thb-cv-kogasa_jolly'


class JollyHandler:
    def choose_card_text(g, act, cards):
        if cards:
            return (False, u'请不要选择牌！')

        return (True, u'(～￣▽￣)～')

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家，该玩家摸一张牌')

        return (True, u'(～￣▽￣)～')


class Surprise:
    # Skill
    name = u'惊吓'

    def clickable(game):
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

    def is_action_valid(g, cl, tl):
        if len(tl) != 1:
            return (False, u'请选择惊吓对象…')

        cl = cl[0].associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张手牌！')

        c, = cl
        if c.is_card(cards.VirtualCard) or c.resides_in.type not in ('cards', 'showncards'):
            return (False, u'请选择一张手牌！')

        # return (True, u'(´・ω・`)')
        return (True, u'\ ( °▽ °) /')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r突然出现在|G【%s】|r面前，伞上'
            u'的大舌头直接糊在了|G【%s】|r的脸上！'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-kogasa_surprise'


class SurpriseAction:
    # choose_option
    choose_option_buttons = (
        (u'黑桃', cards.Card.SPADE),
        (u'红桃', cards.Card.HEART),
        (u'草花', cards.Card.CLUB),
        (u'方片', cards.Card.DIAMOND),
    )

    # choose_option
    choose_option_buttons = (
        (u'♠', cards.Card.SPADE),
        (u'♥', cards.Card.HEART),
        (u'♣', cards.Card.CLUB),
        (u'♦', cards.Card.DIAMOND),
    )

    choose_option_prompt = u'请选择一个花色…'

    def effect_string(act):
        if act.succeeded:
            return u'效果拔群！'
        else:
            return u'似乎没有什么效果'


class Kogasa:
    # Character
    char_name = u'多多良小伞'
    port_image = 'thb-portrait-kogasa'
    figure_image = 'thb-figure-kogasa'
    miss_sound_effect = 'thb-cv-kogasa_miss'
    description = (
        u'|DB愉快的遗忘之伞 多多良小伞 体力：3|r\n\n'
        u'|G惊吓|r：出牌阶段限一次，你可以选择一张手牌和一名角色，该角色选择一种花色后获得这张牌，并将其置入明牌区。若此牌与所选花色不同，则你对该角色造成1点伤害。\n\n'
        u'|G愉快|r：|B锁定技|r，摸牌阶段摸牌后，你令一名角色摸一张牌。\n\n'
        u'|DB（画师：霏茶，CV：VV）|r'
    )
