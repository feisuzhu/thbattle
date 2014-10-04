# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from gamepack.thb import cards
from gamepack.thb.ui.resource import resource as gres
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc

# -- code --
__metaclass__ = gen_metafunc(cards)


class DemolitionCard:
    # action_stage meta
    image = gres.card_demolition
    name = u'城管执法'
    description = (
        u'|R城管执法|r\n\n'
        u'出牌阶段，对一名其他角色使用，弃置其区域内的一张牌。\n\n'
        u'|DB（画师：Pixiv ID 557324，CV：shourei小N）|r'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择拆除目标')

        target = target_list[0]
        if not len(target.cards) + len(target.showncards) + len(target.equips) + len(target.fatetell):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'嗯，你的牌太多了')

    def sound_effect(act):
        return gres.cv.card_demolition


class Demolition:
    def effect_string(act):
        if not act.succeeded: return None
        return u'|G【%s】|r卸掉了|G【%s】|r的%s。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            card_desc(act.card),
        )


class RejectCard:
    # action_stage meta
    name = u'好人卡'
    image = gres.card_reject
    description = (
        u'|R好人卡|r\n\n'
        u'一张符卡对一名目标角色生效前，你可以使用此牌来抵消该符卡对其目标角色产生的效果。\n\n'
        u'|DB（CV：VV）'
    )

    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动出好人卡')

    def effect_string(act):
        return u'|G【%s】|r为|G【%s】|r受到的|G%s|r使用了|G%s|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.force_action.target_act.associated_card.ui_meta.name,
            act.card.ui_meta.name,
        )

    def sound_effect(act):
        return gres.cv.card_reject


class RejectHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        c = act.target_act.associated_card
        name = c.ui_meta.name

        s = u'【%s】受到的【%s】' % (
            act.target_act.target.ui_meta.char_name,
            name,
        )

        if act.cond(cards):
            return (True, u'对不起，你是一个好人(%s)' % s)
        else:
            return (False, u'请选择一张好人卡（%s)' % s)


class SealingArrayCard:
    # action_stage meta
    name = u'封魔阵'
    image = gres.card_sealarray
    tag_anim = lambda c: gres.tag_sealarray
    description = (
        u'|R封魔阵|r\n\n'
        u'延时类符卡\n'
        u'出牌阶段，对一名其他角色使用，将此牌横置于该角色的判定区内。该角色的判定阶段，需进行一次判定然后弃置此牌。若判定结果不为红桃，跳过其出牌阶段。\n'
        u'|B|R>> |r判定开始前,你可以使用【好人卡】抵消该符卡的效果（抵消后弃掉【封魔阵】）。\n\n'
        u'|DB（CV：shourei小N）|r'
    )

    def is_action_valid(g, cl, target_list):
        if len(target_list) != 1:
            return (False, u'请选择封魔阵的目标')
        t = target_list[0]
        if g.me is t:
            return (False, u'你不能跟自己过不去啊！')

        return (True, u'画个圈圈诅咒你！')

    def sound_effect(act):
        return gres.cv.card_sealarray


class SealingArray:
    def effect_string(act):
        tgt = act.target
        if act.succeeded:
            return u'|G【%s】|r被困在了封魔阵中' % tgt.ui_meta.char_name
        else:
            return u'封魔阵没有布置完善，|G【%s】|r侥幸逃了出来' % tgt.ui_meta.char_name


class FrozenFrogCard:
    # action_stage meta
    name = u'冻青蛙'
    image = gres.card_frozenfrog
    tag_anim = lambda c: gres.tag_frozenfrog
    description = (
        u'|R冻青蛙|r\n\n'
        u'延时类符卡\n'
        u'出牌阶段，对一名其他角色使用，将此牌横置于该角色的判定区内。该角色的判定阶段，需进行一次判定然后弃置此牌。若判定结果不为黑桃，跳过其摸牌阶段。\n'
        u'|B|R>> |r判定开始前,你可以使用【好人卡】抵消该符卡的效果(抵消后弃掉【冻青蛙】)。\n\n'
        u'|DB（画师：Pixiv ID 无限轨道A，CV：shourei小N）|r'
    )

    def is_action_valid(g, cl, target_list):
        if len(target_list) != 1:
            return (False, u'请选择冻青蛙的目标')
        t = target_list[0]
        if g.me is t:
            return (False, u'你不能跟自己过不去啊！')

        return (True, u'伸手党什么的，冻住就好了！')

    def sound_effect(act):
        return gres.cv.card_frozenfrog


class FrozenFrog:
    def effect_string(act):
        tgt = act.target
        if act.succeeded:
            return u'|G【%s】|r被冻住了……' % tgt.ui_meta.char_name
        else:
            return u'幻想乡今天大晴，|G【%s】|r没有被冻住~' % tgt.ui_meta.char_name


class NazrinRodCard:
    # action_stage meta
    name = u'寻龙尺'
    image = gres.card_nazrinrod
    description = (
        u'|R寻龙尺|r\n\n'
        u'非延时符卡\n'
        u'出牌阶段使用，从牌堆摸两张牌。\n\n'
        u'|DB（CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'看看能找到什么好东西~')

    def sound_effect(act):
        return gres.cv.card_nazrinrod


class SinsackCard:
    # action_stage meta
    name = u'罪袋'
    image = gres.card_sinsack
    tag_anim = lambda c: gres.tag_sinsack
    description = (
        u'|R罪袋|r\n\n'
        u'延时类符卡\n'
        u'出牌阶段，对你使用，将此牌横置于你的判定区内。判定区内有此牌的角色的判定阶段，需进行一次判定：\n'
        u'|B|R>> |r若判定结果为黑桃1-8，则目标角色受到3点无来源伤害，然后将其置入弃牌堆。\n'
        u'|B|R>> |r若判定结果不在此范围，则将其移动到下家的判定区内。\n'
        u'|B|R>> |r判定开始前,你可以使用【好人卡】抵消该符卡的效果,并将该【罪袋】直接传递给下家。\n\n'
        u'|DB（画师：Pixiv UID 193851，CV：VV/大白）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'别来找我！')

    def sound_effect(act):
        return gres.cv.card_sinsack


class Sinsack:
    def effect_string(act):
        tgt = act.target
        if act.succeeded:
            return u'罪袋终于找到了机会，将|G【%s】|r推倒了…' % tgt.ui_meta.char_name


class SinsackDamage:
    def sound_effect(act):
        return gres.cv.card_sinsack_effect


class YukariDimensionCard:
    # action_stage meta
    image = gres.card_yukaridimension
    name = u'隙间'

    description = (
        u'|R隙间|r\n\n'
        u'出牌阶段，对距离为1的一名其他角色使用，获得其区域内的一张牌。\n\n'
        u'|DB（画师：Pixiv ID 7334440，CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择目标')

        target = target_list[0]
        if not (target.cards or target.showncards or target.equips or target.fatetell):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'请把胖次给我！')

    def sound_effect(act):
        return gres.cv.card_dimension


class YukariDimension:
    def effect_string(act):
        src, tgt = act.source, act.target
        if act.succeeded:
            return u'|G【%s】|r透过隙间拿走了|G【%s】|r的1张牌' % (
                src.ui_meta.char_name,
                tgt.ui_meta.char_name
            )


class DuelCard:
    # action_stage meta
    image = gres.card_duel
    name = u'弹幕战'
    description = (
        u'|R弹幕战|r\n\n'
        u'出牌阶段，对一名其他角色使用，由目标角色开始，轮流打出一张【弹幕】。首先不打出【弹幕】的一方受到另一方造成的1点伤害。\n\n'
        u'|DB（画师：Pixiv ID 8092636，CV：小羽）|r'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择弹幕战的目标')

        return (True, u'来，战个痛快！')

    def sound_effect(act):
        return gres.cv.card_duel


class MapCannonCard:
    image = gres.card_mapcannon
    name = u'地图炮'
    description = (
        u'|R地图炮|r\n\n'
        u'群体符卡\n'
        u'出牌阶段，对除你以外的所有其他角色使用，目标角色需依次打出一张【擦弹】，否则该角色受到1点伤害。\n\n'
        u'|DB（画师：Pixiv ID 24801096，CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'一个都不能跑！')

    def sound_effect(act):
        return gres.cv.card_mapcannon


class SinsackCarnivalCard:
    image = gres.card_sinsackcarnival
    name = u'罪袋狂欢'
    description = (
        u'|R罪袋狂欢|r\n\n'
        u'群体符卡\n'
        u'出牌阶段，对除你以外的所有其他角色使用，目标角色需依次打出一张【弹幕】，否则该角色受到1点伤害。\n\n'
        u'|DB（画师：Pixiv UID 146732，CV：大白）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'罪袋们来送水啦！')

    def sound_effect(act):
        return gres.cv.card_sinsackcarnival


class FeastCard:
    # action_stage meta
    image = gres.card_feast
    name = u'宴会'
    description = (
        u'|R宴会|r\n\n'
        u'群体符卡\n'
        u'出牌阶段，对所有角色使用。已受伤的角色回复一点体力，未受伤的角色获得|B喝醉|r状态。\n\n'
        u'|DB（画师：Pixiv ID 8218978，CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'开宴啦~~')

    def sound_effect(act):
        return random.choice([
            gres.cv.card_feast1,
            gres.cv.card_feast2,
            gres.cv.card_feast3,
        ])


class HarvestCard:
    # action_stage meta
    image = gres.card_harvest
    name = u'五谷丰登'
    description = (
        u'|R五谷丰登|r\n\n'
        u'群体符卡\n'
        u'出牌阶段，对所有角色使用，你从牌堆顶亮出等同于现存角色数量的牌，目标角色依次选择并获得这些牌中的一张。\n\n'
        u'|DB（画师：牛肉かしら，CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'麻薯会有的，节操是没有的！')

    def sound_effect(act):
        return gres.cv.card_harvest


class HarvestEffect:
    def effect_string(act):
        if not act.succeeded: return None
        tgt = act.target
        c = act.card
        return u'|G【%s】|r获得了|G%s|r' % (
            tgt.ui_meta.char_name,
            c.ui_meta.name,
        )


class DollControlCard:
    # action_stage meta
    name = u'人形操控'
    image = gres.card_dollcontrol
    description = (
        u'|R人形操控|r\n\n'
        u'出牌阶段，对装备区内有武器牌的一名其他角色使用，令其选择一项：对其攻击范围内一名由你指定的角色使用一张【弹幕】，或将武器交给你。\n\n'
        u'|DB（画师：Pixiv UID 2957827，CV：小羽）|r'
    )
    custom_ray = True

    def is_action_valid(g, cl, tl):
        n = len(tl)
        if n == 0:
            return (False, u'请选择被控者')

        if tl[0] is g.me:
            return (False, u'你不可以控制你自己')

        if all(e.equipment_category != 'weapon' for e in tl[0].equips):
            return (False, u'被控者没有武器！')

        if n == 1:
            return (False, u'请选择被控者的攻击目标')
        elif n == 2:
            from gamepack.thb import actions, cards
            c = cards.AttackCard()
            lc = actions.LaunchCard(tl[0], [tl[1]], c)
            if not lc.can_fire():
                return (False, u'被控者无法向目标出【弹幕】！')
            return (True, u'乖，听话！')

    def sound_effect(act):
        return gres.cv.card_dollcontrol


class DollControl:
    # choose card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'那好吧…')
        else:
            return (False, u'请出【弹幕】（否则你的武器会被拿走）')

    def ray(act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]


class DonationBoxCard:
    # action_stage meta
    name = u'塞钱箱'
    image = gres.card_donationbox
    description = (
        u'|R塞钱箱|r\n\n'
        u'群体符卡\n'
        u'出牌阶段，对至多两名其他角色使用，目标角色需将自己的一张牌置入你的明牌区。\n\n'
        u'|DB（画师：Pixiv ID 4104174，CV：shourei小N）|r'
    )

    def is_action_valid(g, cl, tl):
        n = len(tl)
        if not n:
            return (False, u'请选择1-2名玩家')

        for t in tl:
            if not (t.cards or t.showncards or t.equips):
                return (False, u'目标没有可以给你的牌')

        return (True, u'纳奉！纳奉！')

    def sound_effect(act):
        return gres.cv.card_donationbox


class DonationBoxEffect:
    # choose card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'这是抢劫啊！')
        else:
            return (False, u'请选择一张牌（否则会随机选择一张）')
