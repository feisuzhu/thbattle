# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.youmu)


class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = gres.youmu_port
    description = (
        u'|DB半分虚幻的厨师 魂魄妖梦 体力：4|r\n\n'
        u'|G迷津慈航斩|r：|B锁定技|r，你使用【弹幕】时，目标角色需连续使用两张【擦弹】才能抵消；与你进行【弹幕战】的角色每次需连续打出两张【弹幕】。\n\n'
        u'|G二刀流|r：你可以同时装备两把武器。同时装备时，攻击距离加成按其中较低者计算，武器技能同时有效。\n'
        u'|B|R>> |r成为【人形操控】目标并且不出【弹幕】的话，两把武器会被一起拿走\n\n'
        u'|R现世妄执|r：|B觉醒技|r，当你同时装备了楼观剑与白楼剑时，你需提高一点体力上限并回复一点体力，获得此技能（卸掉/更换装备不会失去）。一回合内你可以使用两张【弹幕】。'
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


class Nitoryuu:
    # Skill
    name = u'二刀流'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Xianshiwangzhi:
    # Skill
    name = u'现世妄执'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
