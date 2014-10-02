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
        u'出牌阶段对(除自己外)任意一名玩家使用，随机抽取并弃掉对方一张手牌，或选择并弃掉一张对方面前的牌(包括装备、明牌区和判定区内延时类符卡)。\n\n'
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
        u'目标符卡对目标角色生效前，对目标符卡使用。抵消该符卡对其指定的一名目标角色产生的效果。\n\n'
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
        u'出牌阶段对任意一名玩家使用,将此牌置于目标玩家判定区,对方在其判定阶段需判定——如果判定结果为红桃，则照常行动，弃掉【封魔阵】；如果判定结果不是红桃，则该回合跳过出牌阶段（照常摸牌和弃牌），弃掉【封魔阵】。\n'
        u'|B|R>> |r仅当需要开始进行【封魔阵】的判定时,才能使用【好人卡】抵消之(抵消后弃掉【封魔阵】)。\n\n'
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
        u'出牌阶段对任意一名玩家使用,将此牌置于目标玩家判定区,对方在其摸牌阶段需判定——如果判定结果不为黑桃，则该回合跳过摸牌阶段。无论判定是否成功，弃掉该【冻青蛙】。\n'
        u'|B|R>> |r仅当需要开始进行【冻青蛙】的判定时,才能使用【好人卡】抵消之(抵消后弃掉【冻青蛙】)。\n\n'
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
        u'出牌阶段使用,将【罪袋】横置于自己面前:\n'
        u'|B|R>> |r【罪袋】将一直放在那里直到这回合结束,当自己下回合进入回合开始阶段时,自己需要判定——若判定结果为黑桃1~黑桃8的牌,视为被【罪袋】推倒,受到3点伤害,并将【罪袋】弃掉;否则,将【罪袋】传给右边的玩家,右边的玩家在他/她的回合开始阶段需要做同样的判定,以此类推,直到【罪袋】生效为止,弃掉【罪袋】。\n'
        u'|B|R>> |r仅当需要开始进行【罪袋】的判定时,才能使用【好人卡】抵消之,但抵消后不弃掉【罪袋】,而是将之传递给下家。\n\n'
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
        u'出牌阶段对距离为1的一名玩家使用，随机抽取并获得对方一张手牌，或选择并获得一张对方面前的牌(包括装备、明牌区内的牌和判定区的延时类符卡)。\n\n'
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
        u'出牌阶段对(除自己外)任意一名玩家使用，由目标角色先开始，你和他（她）轮流打出一张【弹幕】，【弹幕战】对首先不出【弹幕】的一方造成1点伤害；另一方成为此伤害的来源。\n\n'
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
        u'按行动顺序结算，除非目标角色打出一张【擦弹】，否则该角色受到【地图炮】对其造成的1点伤害。\n\n'
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
        u'出牌阶段使用，所有其他玩家需打出一张【弹幕】，否则受到一点伤害。\n\n'
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
        u'对所有玩家生效，每一个体力不满的玩家回复一点体力，满体力玩家获得|B喝醉|r状态。\n\n'
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
        u'你从牌堆顶亮出等同于现存角色数量的牌，然后所有角色按行动顺序结算，选择并获得这些牌中的一张。\n\n'
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
        u'对装备有武器的玩家使用，令其使用一张【弹幕】攻击另一名指定玩家，否则将武器交给自己。\n\n'
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
        u'指定1-2名有手牌或装备的玩家，被指定玩家必须选择一张手牌或装备牌置入你的明牌区。\n\n'
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
