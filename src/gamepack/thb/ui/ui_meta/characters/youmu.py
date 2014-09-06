# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.youmu)


class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = gres.youmu_port
    miss_sound_effect = gres.cv.youmu_miss
    description = (
        u'|DB半分虚幻的厨师 魂魄妖梦 体力：4|r\n\n'
        u'|G迷津慈航斩|r：|B锁定技|r，你使用【弹幕】时，目标角色需连续使用两张【擦弹】才能抵消；与你进行【弹幕战】的角色每次需连续打出两张【弹幕】。\n\n'
        u'|G二刀流|r：你可以同时装备两把武器。同时装备时，攻击距离加成按其中较低者计算，武器技能同时有效，且你于出牌阶段可以额外使用一张弹幕。\n'
        u'|B|R>> |r成为【人形操控】目标并且不出【弹幕】的话，两把武器会被一起拿走\n'
        u'|B|R>> |r当你同时装备两把武器时，你可以主动的弃置其中一把\n\n'
        u'|DB（画师：【植田亮東方画集】蜻蛉Akizu-Ueda.Ryo，CV：小羽）|r'

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
        return gres.cv.youmu_mjchz


class YoumuWearEquipmentAction:
    def sound_effect(act):
        card = act.associated_card
        tgt = act.target
        equips = tgt.equips
        cat = card.equipment_category
        if cat == 'weapon' and [e for e in equips if e.equipment_category == 'weapon']:
            return gres.cv.youmu_nitoryuu


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
