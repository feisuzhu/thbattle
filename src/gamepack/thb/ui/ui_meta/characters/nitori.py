# -*- coding: utf-8 -*-

# -- third party --
# -- own --
from gamepack.thb import characters, actions
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.nitori)


class Science:
    # Skill
    name = u'科学'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ScienceAction:
    def effect_string_before(act):
        return u'|G【%s】|r使用了|G科学|r。' % (
            act.source.ui_meta.char_name,
        )

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'给你牌~')


class ScienceHandler:
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【科学】吗？'


class Dismantle:
    # Skill
    name = u'拆解'

    def clickable(g):
        skill = characters.nitori.Dismantle(g.me)
        return skill.ui_meta.clickable(g)


class DismantleOwn:
    def effect_string(act):
        return u'|G【%s】|r|G拆解|r了%s。' % (
            act.source.ui_meta.char_name,
            card_desc(act.card.associated_cards),
        )

    def clickable(game):
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True

        except IndexError:
            pass

        return False

    def is_action_valid(g, cl, tl):
        cl = cl[0].associated_cards
        if not cl or len(cl) != 1:
            return (False, u'请选择一张装备')

        if 'equipment' not in cl[0].category:
            return (False, u'请选择一张装备')

        return (True, u'拆解！')


class ForcedDismantle:
    def clickable(game):
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True

        except IndexError:
            pass

        return False

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌！')

        if not len(tl):
            return (False, u'请选择一名玩家')

        return (True, u'拆解！')


class DismantleHandler:
    choose_option_buttons = ((u'自己', 'own'), (u'其他角色', 'forced'))
    choose_option_prompt = u'请选择本回合【拆解】的效果的对象'


class Nitori:
    # Character
    char_name = u'河城荷取'
    port_image = 'thb-portrait-nitori'
    description = (
        u'|DB水中的工程师 河城荷取 体力：3|r\n'
        u'\n'
        u'|G拆解|r：出牌阶段开始时，你选择获得一个效果，直到本回合结束\n'
        u'|B|R>> |r出牌阶段你可以|B重铸|r自己的装备牌\n'
        u'|B|R>> |r出牌阶段限一次，你可以|B重铸|r一名其他角色装备区的一张牌，然后其摸一张牌。\n'
        u'\n'
        u'|G科学|r：当你于回合外因使用、打出、弃置而失去牌后，若牌中至少有一张基本牌，你可以进行一次判定，若为非基本牌，你可以将该判定牌交给一名角色。'
    )
