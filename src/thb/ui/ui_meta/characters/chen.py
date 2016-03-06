# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, cards, characters
from thb.ui.ui_meta.common import gen_metafunc
from utils import BatchList

# -- code --
__metaclass__ = gen_metafunc(characters.chen)


class FlyingSkanda:
    # Skill
    name = u'飞翔韦驮天'

    def clickable(game):
        me = game.me
        if me.tags['flying_skanda'] >= me.tags['turn_count']: return False
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择一张牌！')
        c = acards[0]

        while True:
            if c.is_card(cards.AttackCard): break

            rst = c.is_card(cards.RejectCard)
            rst = rst or c.is_card(cards.DollControlCard)
            rst = (not rst) and issubclass(c.associated_action, cards.InstantSpellCardAction)
            if rst: break

            return (False, u'请选择一张【弹幕】或者除【人形操控】与【好人卡】之外的非延时符卡！')

        if len(target_list) != 2:
            return (False, u'请选择目标（2名玩家）')

        if g.me is target_list[-1]:
            return (False, u'不允许选择自己')
        else:
            return (True, u'喵！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card.associated_cards[0]
        tl = BatchList(act.target_list)

        if card.is_card(cards.AttackCard):
            s = u'弹幕掺了金坷垃，攻击范围一千八！'
        else:
            s = u'符卡掺了金坷垃，一张能顶两张用！'

        return u'|G【%s】|r：“%s|G【%s】|r接招吧！”' % (
            source.ui_meta.char_name,
            s,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

    def sound_effect(act):
        return 'thb-cv-chen_skanda'


class Shikigami:
    # Skill
    name = u'式神'

    def clickable(game):
        me = game.me
        if me.tags.get('shikigami_tag'): return False
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return (False, u'请不要选择牌')

        if not tl:
            return (False, u'请选择一名玩家')
        else:
            return (True, u'发动【式神】')

    def sound_effect(act):
        return 'thb-cv-chen_shikigami'


class ShikigamiAction:
    choose_option_buttons = ((u'摸2张牌', False), (u'回复1点体力', True))
    choose_option_prompt = u'请为受到的【式神】选择效果'


class Chen:
    # Character
    char_name = u'橙'
    port_image = 'thb-portrait-chen'
    figure_image = 'thb-figure-chen'
    miss_sound_effect = 'thb-cv-chen_miss'
    description = (
        u'|DB凶兆的黑喵 橙 体力：4|r\n\n'
        u'|G飞翔韦驮天|r：出牌阶段限一次，你使用【弹幕】或除了【人形操控】以外的非延时单体符卡时，可以额外指定一个目标。\n\n'
        u'|G式神|r：|B限定技|r，出牌阶段，你可以令一名其他角色选择一项：摸2张牌或回复一点体力。直到你的下个回合开始，你和该角色可以于自己的回合内对对方攻击范围内的角色使用【弹幕】。\n\n'
        u'|DB（画师：和茶，CV：shourei小N）|r'
    )
