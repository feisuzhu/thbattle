# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.yugi)


class Yugi:
    # Character
    char_name = u'星熊勇仪'
    port_image = gres.yugi_port
    description = (
        u'|DB人所谈论的怪力乱神 星熊勇仪 体力：4|r\n\n'
        #u'|G强袭|r：你可以自损1点体力，或者使用一张武器牌/【酒】，对任意一名在你的攻击范围内的玩家造成一点伤害。\n\n'
        u'|G强袭|r：你与其他玩家结算距离时始终-1\n\n'
        u'|G怪力|r：你对别的角色出【弹幕】时可以选择做一次判定：若判定牌为红色花色，则此【弹幕】不可回避，直接命中；若判定牌为黑色花色，则此【弹幕】可回避，但如果对方没有出【擦弹】，则命中后可以选择弃掉对方一张牌。'
    )


class AssaultSkill:
    # Skill
    name = u'强袭'
    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FreakingPowerSkill:
    # Skill
    name = u'怪力'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FreakingPower:
    def effect_string_before(act):
        return u'|G【%s】|r稍微认真了一下，弹幕以惊人的速度冲向|G【%s】|r' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class YugiHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【怪力】吗？'
