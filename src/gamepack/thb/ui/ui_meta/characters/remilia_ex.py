# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import cards, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from utils import BatchList

# -- code --
__metaclass__ = gen_metafunc(characters.remilia_ex)


remilia_ex_description = (
    u'|DB永远威严的红月 蕾米莉亚 体力：6|r\n\n'
    u'|G神枪|r：出现以下情况之一，你可以令你的【弹幕】不能被【擦弹】抵消：\n'
    u'|B|R>> |r目标角色的体力值 大于 你的体力值。\n'
    u'|B|R>> |r目标角色的手牌数 小于 你的手牌数。\n\n'
    u'|G红魔之吻|r：|B锁定技|r，当你使用红色【弹幕】对一名其他角色造成伤害后，你回复1点体力。\n\n'
    u'|G不夜城|r：|DB信仰消耗3|r，出牌阶段限一次。你依次弃置所有解决者的一张手牌或装备牌。如果解决者无牌可弃，则弃置所有信仰。\n\n'
    u'|B|R=== 以下是变身后获得的技能 ===|r\n\n'
    u'|G碎心|r：|DB信仰消耗4|r。出牌阶段，你可以视为对一名其他角色使用了一张红色的【弹幕】。以此法使用的弹幕不可闪避且伤害+1。\n\n'
    u'|G红雾|r：出牌阶段限一次，你可以弃置一张红色手牌，令所有解决者依次对另一名解决者使用一张【弹幕】，否则失去1点体力。\n\n'
    u'|G七重奏|r：|B锁定技|r，解决者对你使用延时符卡时，需额外弃置一张颜色相同的符卡，否则取消之。\n\n'
    u'|G夜王|r：|B锁定技|r，出牌阶段开始时，你摸4张牌。你的手牌上限+3。\n\n'
    u'|DB（画师：Pixiv ID 38850756, 421918）|r'
)


class RemiliaEx:
    # Character
    char_name = u'异·蕾米莉亚'
    port_image = 'thb-portrait-remilia_ex'
    description = remilia_ex_description


class RemiliaEx2:
    # Character
    char_name = u'异·蕾米莉亚'
    port_image = 'thb-portrait-remilia_ex2'
    description = remilia_ex_description

    wallpaper = 'thb-remilia_ex_wallpaper'
    bgm = 'thb-bgm_remilia_ex'
    color_scheme = 'red'


class HeartBreak:
    # Skill
    name = u'碎心'

    def effect_string(act):
        return u'|G【%s】|r将信仰灌注在神枪里，向|G【%s】|r使用了|G碎心|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def clickable(g):
        me = g.me
        if len(me.faiths) < 4: return False
        return True

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌')

        if not tl:
            return (False, u'请选择一名解决者')

        return (True, u'发动碎心')


class NeverNight:
    # Skill
    name = u'不夜城'

    def effect_string(act):
        tl = BatchList(act.target_list)
        return u'|G【%s】|r使用了3点信仰，向|G【%s】|r使用了|G不夜城|r。' % (
            act.source.ui_meta.char_name,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

    def clickable(g):
        me = g.me
        if not my_turn(): return False
        if len(me.faiths) < 3: return False
        if limit1_skill_used('nevernight_tag'): return False
        return True

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌')

        if not tl:
            return (False, u'WTF?!')

        return (True, u'发动不夜城')


class ScarletFogEffect:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'红雾里看不清，先来一发再说！')
        else:
            return (False, u'请对另一名解决者使用一张【弹幕】（否则失去一点体力）')

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'请对另一名解决者使用一张【弹幕】（否则失去一点体力）')

        return (True, u'红雾里看不清，先来一发再说！')


class ScarletFog:
    # Skill
    name = u'红雾'

    def effect_string(act):
        tl = BatchList(act.target_list)
        return u'|G【%s】|r向|G【%s】|r发动了|G红雾|r！' % (
            act.source.ui_meta.char_name,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

    def clickable(g):
        if not my_turn(): return False
        if limit1_skill_used('scarletfog_tag'): return False
        return True

    def is_action_valid(g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, u'请选择一张红色手牌')

        card = acards[0]

        if card.color != cards.Card.RED or card.resides_in.type not in ('cards', 'showncards'):
            return (False, u'请选择一张红色的手牌!')

        if card.is_card(cards.Skill):
            return (False, u'你不可以像这样组合技能')

        if not tl:
            return (False, u'WTF?!')

        return (True, u'发动红雾')


class QueenOfMidnight:
    # Skill
    name = u'夜王'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Septet:
    # Skill
    name = u'七重奏'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SeptetHandler:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置并使延时符卡生效')
        else:
            return (False, u'【七重奏】请选择一张颜色相同的符卡弃置')
