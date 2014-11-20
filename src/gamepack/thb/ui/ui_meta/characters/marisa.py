# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn

# -- code --
__metaclass__ = gen_metafunc(characters.marisa)


class Marisa:
    # Character
    char_name = u'雾雨魔理沙'
    port_image = 'thb-portrait-marisa'
    miss_sound_effect = 'thb-cv-marisa_miss'
    description = (
        u'|DB绝非普通的强盗少女 雾雨魔理沙 体力：4|r\n\n'
        u'|G借走|r：出牌阶段限一次，你可以获得一名其他角色的一张牌，然后视为该角色对你使用了一张【弹幕】。\n\n'
        u'|DB（画师：Pixiv ID 3812034，CV：君寻）|r'
    )


class Daze:
    name = u'打贼'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r喊道：“打贼啦！”向|G【%s】|r使用了|G弹幕|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class Borrow:
    # Skill
    name = u'借走'

    def clickable(g):
        if limit1_skill_used('borrow_tag'):
            return False

        if not my_turn(): return False

        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        if skill.associated_cards:
            return (False, u'请不要选择牌!')

        if len(target_list) != 1:
            return (False, u'请选择1名玩家')

        tgt = target_list[0]
        if not (tgt.cards or tgt.showncards or tgt.equips):
            return (False, u'目标没有牌可以“借给”你')

        return (True, u'我死了以后你们再拿回去好了！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'大盗|G【%s】|r又出来“|G借走|r”了|G【%s】|r的牌。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-marisa_borrow'
