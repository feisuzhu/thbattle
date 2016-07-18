# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.satori20150804)


class MindReadLimit:
    target_independent = True
    shootdown_message = u'【读心】你不能使用明牌区的黑色牌'


class MindRead:
    name = u'读心'
    description = u'出牌阶段限一次，你可以将一名角色的一张手牌置于明牌区，且该角色当前回合内无法使用明牌区的黑色牌。'

    def clickable(game):
        me = game.me
        return my_turn() and not ttags(me)['mind_read']

    def is_action_valid(g, cl, tl):
        if len(tl) != 1:
            return (False, u'请选择读心对象…')

        cl = cl[0].associated_cards
        if len(cl) != 0:
            return (False, u'请不要选择牌！')

        return (True, u'MIND READ!')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r对|G【%s】|r发动了|G读心|r。'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class RosaHandler:
    choose_option_prompt = u'你要发动【蔷薇】吗（【读心】效果）？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class Rosa:
    # Skill
    name = u'蔷薇'
    description = u'每当你受到一名角色的一次伤害后，或你对一名角色造成一次伤害后，若此伤害不由群体符卡造成，可以立即对该角色发动一次|G读心|r。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class HeartfeltFancyHandler:
    choose_option_prompt = u'你要发动【心花】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class HeartfeltFancyAction:

    def sound_effect(act):
        return 'thb-cv-suika_drunkendream'

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'选择的玩家摸一张牌')


class HeartfeltFancy:
    name = u'心花'
    description = u'当一名角色的明牌区内牌数增加至大于或等于两张时，你可以重铸该角色明牌区内的一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Satori20150804:
    # Character
    name        = u'古明地觉'
    title       = u'怨灵也为之惧怯的少女'
    designer    = u'帕秋莉.诺蕾姬'

    port_image        = u'thb-portrait-satori20150804'
