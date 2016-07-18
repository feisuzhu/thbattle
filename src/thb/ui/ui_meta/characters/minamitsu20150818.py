# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_is_action_valid, passive_clickable


# -- code --
__metaclass__ = gen_metafunc(characters.minamitsu20150818)


class Shipwreck:
    # Skill
    name = u'水难'
    description = u'弃牌阶段开始时，你可令一名角色交给你一张牌，然后你须将本阶段你弃置的牌交给该角色，若此时其手牌数大于其当前体力值，其失去一点体力。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ShipwreckChooseCard:

    def choose_card_text(g, act, cl):
        if act.cond(cl):
            return True, u'水难：交出这张牌'
        else:
            return False, u'水难：请交出一张牌'

    def effect_string_before(act):
        return u'“把勺子借给我吧！”|G【%s】|r对|G【%s】|r说。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def effect_string(act):
        return u'|G【%s】|r交出了一张牌。' % (
            act.target.ui_meta.name,
        )


class ShipwreckDropCardStage:

    def choose_card_text(g, act, cl):
        if act.cond(cl):
            return True, u'水难：交出这些牌'
        else:
            return False, u'水难：请选择%s张牌交给对方' % act.dropn

    def effect_string(act):
        return


class ShipwreckBrokenScoop:

    def effect_string_before(act):
        return u'然而|G【%s】|r拿到的勺子是漏的，并没有什么卵用。' % (
            act.source.ui_meta.name,
        )


class ShipwreckEffect:

    def effect_string_before(act):
        return u'|G【%s】|r开始灌水！|G【%s】|r灌了%s桶水！' % (
            act.source.ui_meta.name,
            act.source.ui_meta.name,
            len(act.cards),
        )

    def effect_string(act):
        bh = u'|G【%s】|r大破！' if act.life_lost else u'不过|G【%s】|r貌似挺能喝的嘛……'
        return bh % act.target.ui_meta.name


class ShipwreckHandler:

    def target(pl):
        if not pl:
            return (False, u'水难：请选择1名玩家（否则不发动）')

        return (True, u'发动水难')


class Minamitsu20150818:
    # Character
    name        = u'村纱水蜜'
    title       = u'水难事故的念缚灵'
    designer    = u'冰DIO师'

    port_image        = u'thb-portrait-minamitsu20150818'
