# -*- coding: utf-8 -*-


# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid


# -- code --


@ui_meta(characters.youmu.Youmu)
class Youmu:
    # Character
    name        = '魂魄妖梦'
    title       = '半分虚幻的厨师'
    illustrator = '霏茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-youmu'
    figure_image      = 'thb-figure-youmu'
    miss_sound_effect = 'thb-cv-youmu_miss'


@ui_meta(characters.youmu.Mijincihangzhan)
class Mijincihangzhan:
    # Skill
    name = '迷津慈航斩'
    description = '|B锁定技|r，你使用的|G弹幕|r需要连续使用两张|G擦弹|r来抵消；与你进行|G弹幕战|r的角色每次需要连续打出两张|G弹幕|r。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.youmu.MijincihangzhanAttack)
class MijincihangzhanAttack:
    def effect_string_apply(self, act):
        src = act.source
        return '|G【%s】|r在弹幕中注入了妖力，弹幕形成了一个巨大的光刃，怕是不能轻易地闪开的！' % (
            src.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-youmu_mjchz'


@ui_meta(characters.youmu.NitoryuuWearEquipmentAction)
class NitoryuuWearEquipmentAction:
    def sound_effect(self, act):
        card = act.card
        tgt = act.target
        equips = tgt.equips
        cat = card.equipment_category
        if cat == 'weapon' and [e for e in equips if e.equipment_category == 'weapon']:
            return 'thb-cv-youmu_nitoryuu'


@ui_meta(characters.youmu.Nitoryuu)
class Nitoryuu:
    # Skill
    name = '二刀流'
    description = (
        '你可以额外装备一把武器，当你同时装备了两把武器时，攻击范围按其中较高者计算；武器技能同时有效，且你额外增加一点干劲。\n'
        '|B|R>> |r当你受到|G人形操控|r的效果生效时，需交出全部的武器。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    def effect_string(self, act):
        return '|G【%s】|r弃置了自己的一把武器' % (
            act.target.ui_meta.name,
        )
