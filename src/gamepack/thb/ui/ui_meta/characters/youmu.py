# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.youmu)


class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = 'thb-portrait-youmu'
    figure_image = 'thb-figure-youmu'
    miss_sound_effect = 'thb-cv-youmu_miss'
    description = (
        u'|DB半分虚幻的厨师 魂魄妖梦 体力：4|r\n\n'
        u'|G迷津慈航斩|r：|B锁定技|r，你使用的|G弹幕|r目标角色需连续使用两张|G擦弹|r才能抵消；与你进行|G弹幕战|r的角色每次需连续打出两张|G弹幕|r。\n\n'
        u'|G二刀流|r：你可以同时装备两把武器。同时装备时，攻击距离加成按其中较高者计算，武器技能同时有效，且你于出牌阶段可以额外使用一张弹幕。\n'
        u'|B|R>> |r当你受到|G人形操控|r的效果生效时，需交出全部的武器。\n'
        u'|B|R>> |r当你装备两把武器时，你可以主动弃置其中的一把。\n'
        u'\n'
        u'|DB（画师：霏茶，CV：小羽）|r'
    )


class Mijincihangzhan:
    # Skill
    name = u'迷津慈航斩'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MijincihangzhanAttack:
    def effect_string_apply(act):
        src = act.source
        return u'|G【%s】|r在弹幕中注入了妖力，弹幕形成了一个巨大的光刃，怕是不能轻易地闪开的！' % (
            src.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-youmu_mjchz'


class YoumuWearEquipmentAction:
    def sound_effect(act):
        card = act.associated_card
        tgt = act.target
        equips = tgt.equips
        cat = card.equipment_category
        if cat == 'weapon' and [e for e in equips if e.equipment_category == 'weapon']:
            return 'thb-cv-youmu_nitoryuu'


class Nitoryuu:
    # Skill
    name = u'二刀流'

    def clickable(game):
        me = game.me
        weapons = [e for e in me.equips if e.equipment_category == 'weapon']
        return my_turn() and len(weapons) == 2

    def is_action_valid(g, cl, target_list):
        skill = cl[0]

        if not [g.me] == target_list:
            return (False, 'BUG!!')

        if skill.associated_cards:
            return (False, u'请不要选择牌！')

        return (True, u'二刀流：主动弃置一把武器')

    def effect_string(act):
        return u'|G【%s】|r弃置了自己的一把武器' % (
            act.target.ui_meta.char_name,
        )
