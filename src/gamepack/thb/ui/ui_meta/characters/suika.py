# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import actions, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.suika)


class Drunkard:
    # Skill
    name = u'酒鬼'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and act.target is me and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        from gamepack.thb.cards import Card
        if not (
            cl and len(cl) == 1 and
            cl[0].color == Card.BLACK and
            cl[0].resides_in.type in ('cards', 'showncards', 'equips')
        ): return (False, u'请选择一张黑色牌！')
        return (True, u'常在地狱走，怎能没有二锅头！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        s = u'|G【%s】|r不知从哪里拿出一瓶酒，大口喝下。' % (
            source.ui_meta.char_name,
        )
        return s

    def sound_effect(act):
        return 'thb-cv-suika_drunkard'


class GreatLandscape:
    # Skill
    name = u'大江山'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class WineGod:
    # Skill
    name = u'醉神'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class WineDream:
    # Skill
    name = u'醉梦'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class WineGodAwake:
    def effect_string_before(act):
        return u'|G【%s】|r找到了自己的本命酒胡芦……喂这样喝没问题吗？' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-suika_winegod'


class Suika:
    # Character
    char_name = u'伊吹萃香'
    port_image = 'thb-portrait-suika'
    miss_sound_effect = 'thb-cv-suika_miss'
    description = (
        u'|DB小小的酒鬼夜行 伊吹萃香 体力：4|r\n\n'
        u'|G大江山|r：|B锁定技|r，若你没有装备武器牌，你的攻击范围始终+X。（X为你已损失的体力数）\n\n'
        u'|G酒鬼|r：出牌阶段，你可以将一张黑色牌当【酒】使用。\n\n'
        u'|G醉神|r：|B觉醒技|r，当你装备【伊吹瓢】时，你须减少1点体力上限，并永久获得技能|R醉梦|r\n\n'
        u'|R醉梦|r：|B锁定技|r，当你失去喝醉状态时，你摸1张牌。\n\n'
        u'|DB（画师：Pixiv ID 1163421，CV：shourei小N）|r'
    )
