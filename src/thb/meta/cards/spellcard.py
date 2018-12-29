# -*- coding: utf-8 -*-

# -- stdlib --
import itertools
import random

# -- third party --
# -- own --
from thb.cards import definition, spellcard
from thb.meta.common import card_desc, ui_meta


# -- code --
@ui_meta(definition.DemolitionCard)
class DemolitionCard:
    # action_stage meta
    image = 'thb-card-demolition'
    name = '城管执法'
    description = (
        '|R城管执法|r\n\n'
        '出牌阶段，对一名其他角色使用，弃置其区域内的一张牌。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        if not target_list:
            return (False, '请选择拆除目标')

        tgt = target_list[0]
        if not sum([len(l) for l in [tgt.cards, tgt.showncards, tgt.equips, tgt.fatetell]]):
            return (False, '这货已经没有牌了')
        else:
            return (True, '嗯，你的牌太多了')

    def sound_effect(self, act):
        return 'thb-cv-card_demolition'


@ui_meta(spellcard.Demolition)
class Demolition:
    def effect_string(self, act):
        if not act.succeeded: return None
        return '|G【%s】|r卸掉了|G【%s】|r的%s。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card),
        )


@ui_meta(definition.RejectCard)
class RejectCard:
    # action_stage meta
    name = '好人卡'
    image = 'thb-card-reject'
    description = (
        '|R好人卡|r\n\n'
        '一张符卡对一名目标角色生效前，你可以使用此牌来抵消该符卡对其目标角色产生的效果。\n\n'
        '|DB（画师：霏茶，CV：VV）'
    )

    def is_action_valid(self, g, cl, target_list):
        return (False, '你不能主动出好人卡')

    def effect_string(self, act):
        return '|G【%s】|r为|G【%s】|r受到的|G%s|r使用了|G%s|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            act.force_action.target_act.associated_card.ui_meta.name,
            act.card.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-card_reject'

    def has_reject_card(self, p):
        from thb.cards.definition import RejectCard as RC
        if any([c.is_card(RC) for c in itertools.chain(p.cards, p.showncards)]):
            return True

        from thb.characters import reimu
        if p.has_skill(reimu.SpiritualAttack) and not p.dead:
            return True

        return False


@ui_meta(spellcard.RejectHandler)
class RejectHandler:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        c = act.target_act.associated_card
        name = c.ui_meta.name

        s = '【%s】受到的【%s】' % (
            act.target_act.target.ui_meta.name,
            name,
        )

        if act.cond(cards):
            return (True, '对不起，你是一个好人(%s)' % s)
        else:
            return (False, '请选择一张好人卡（%s)' % s)


@ui_meta(definition.SealingArrayCard)
class SealingArrayCard:
    # action_stage meta
    name = '封魔阵'
    image = 'thb-card-sealarray'
    tag_anim = lambda c: 'thb-tag-sealarray'
    description = (
        '|R封魔阵|r\n\n'
        '延时类符卡\n'
        '出牌阶段，对一名其他角色使用，将此牌横置于该角色的判定区内。该角色的判定阶段，需进行一次判定然后弃置此牌。若判定结果不为红桃，跳过其出牌阶段。\n'
        '|B|R>> |r判定开始前,你可以使用【好人卡】抵消该符卡的效果（抵消后弃掉【封魔阵】）。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        if len(target_list) != 1:
            return (False, '请选择封魔阵的目标')
        t = target_list[0]
        if g.me is t:
            return (False, '你不能跟自己过不去啊！')

        return (True, '画个圈圈诅咒你！')

    def sound_effect(self, act):
        return 'thb-cv-card_sealarray'


@ui_meta(spellcard.SealingArray)
class SealingArray:
    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return '|G【%s】|r被困在了封魔阵中' % tgt.ui_meta.name
        else:
            return '封魔阵没有布置完善，|G【%s】|r侥幸逃了出来' % tgt.ui_meta.name


@ui_meta(definition.FrozenFrogCard)
class FrozenFrogCard:
    # action_stage meta
    name = '冻青蛙'
    image = 'thb-card-frozenfrog'
    tag_anim = lambda c: 'thb-tag-frozenfrog'
    description = (
        '|R冻青蛙|r\n\n'
        '延时类符卡\n'
        '出牌阶段，对一名其他角色使用，将此牌横置于该角色的判定区内。该角色的判定阶段，需进行一次判定然后弃置此牌。若判定结果不为黑桃，跳过其摸牌阶段。\n'
        '|B|R>> |r判定开始前,你可以使用【好人卡】抵消该符卡的效果(抵消后弃掉【冻青蛙】)。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        if len(target_list) != 1:
            return (False, '请选择冻青蛙的目标')
        t = target_list[0]
        if g.me is t:
            return (False, '你不能跟自己过不去啊！')

        return (True, '伸手党什么的，冻住就好了！')

    def sound_effect(self, act):
        return 'thb-cv-card_frozenfrog'


@ui_meta(spellcard.FrozenFrog)
class FrozenFrog:
    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return '|G【%s】|r被冻住了……' % tgt.ui_meta.name
        else:
            return '幻想乡今天大晴，|G【%s】|r没有被冻住~' % tgt.ui_meta.name


@ui_meta(definition.NazrinRodCard)
class NazrinRodCard:
    # action_stage meta
    name = '寻龙尺'
    image = 'thb-card-nazrinrod'
    description = (
        '|R寻龙尺|r\n\n'
        '非延时符卡\n'
        '出牌阶段使用，从牌堆摸两张牌。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        return (True, '看看能找到什么好东西~')

    def sound_effect(self, act):
        return 'thb-cv-card_nazrinrod'


@ui_meta(definition.SinsackCard)
class SinsackCard:
    # action_stage meta
    name = '罪袋'
    image = 'thb-card-sinsack'
    tag_anim = lambda c: 'thb-tag-sinsack'
    description = (
        '|R罪袋|r\n\n'
        '延时类符卡\n'
        '出牌阶段，对你使用，将此牌横置于你的判定区内。判定区内有此牌的角色的判定阶段，需进行一次判定：\n'
        '|B|R>> |r若判定结果为黑桃1-8，则目标角色受到3点无来源伤害，然后将其置入弃牌堆。\n'
        '|B|R>> |r若判定结果不在此范围，则将其移动到下家的判定区内。\n'
        '|B|R>> |r判定开始前,你可以使用|B好人卡|r抵消该符卡的效果,并将该|G罪袋|r直接传递给下家。\n\n'
        '|DB（画师：霏茶，CV：VV/大白）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        return (True, '别来找我！')

    def sound_effect(self, act):
        return 'thb-cv-card_sinsack'


@ui_meta(spellcard.Sinsack)
class Sinsack:
    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return '罪袋终于找到了机会，将|G【%s】|r推倒了…' % tgt.ui_meta.name


@ui_meta(spellcard.SinsackDamage)
class SinsackDamage:
    def sound_effect(self, act):
        return 'thb-cv-card_sinsack_effect'


@ui_meta(definition.YukariDimensionCard)
class YukariDimensionCard:
    # action_stage meta
    image = 'thb-card-yukaridimension'
    name = '隙间'

    description = (
        '|R隙间|r\n\n'
        '出牌阶段，对距离为1的一名其他角色使用，获得其区域内的一张牌。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        if not target_list:
            return (False, '请选择目标')

        target = target_list[0]
        if not (target.cards or target.showncards or target.equips or target.fatetell):
            return (False, '这货已经没有牌了')
        else:
            return (True, '请把胖次给我！')

    def sound_effect(self, act):
        return 'thb-cv-card_dimension'


@ui_meta(spellcard.YukariDimension)
class YukariDimension:
    def effect_string(self, act):
        src, tgt = act.source, act.target
        if act.succeeded:
            return '|G【%s】|r透过隙间拿走了|G【%s】|r的1张牌' % (
                src.ui_meta.name,
                tgt.ui_meta.name
            )


@ui_meta(definition.DuelCard)
class DuelCard:
    # action_stage meta
    image = 'thb-card-duel'
    name = '弹幕战'
    description = (
        '|R弹幕战|r\n\n'
        '出牌阶段，对一名其他角色使用，由目标角色开始，轮流打出一张【弹幕】。首先不打出【弹幕】的一方受到另一方造成的1点伤害。\n\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        if not target_list:
            return (False, '请选择弹幕战的目标')

        return (True, '来，战个痛快！')

    def sound_effect(self, act):
        return 'thb-cv-card_duel'


@ui_meta(definition.MapCannonCard)
class MapCannonCard:
    image = 'thb-card-mapcannon'
    name = '地图炮'
    description = (
        '|R地图炮|r\n\n'
        '群体符卡\n'
        '出牌阶段，对除你以外的所有其他角色使用，目标角色需依次打出一张【擦弹】，否则该角色受到1点伤害。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        return (True, '一个都不能跑！')

    def sound_effect(self, act):
        return 'thb-cv-card_mapcannon'


@ui_meta(definition.DemonParadeCard)
class DemonParadeCard:
    image = 'thb-card-demonparade'
    name = '百鬼夜行'
    description = (
        '|R百鬼夜行|r\n\n'
        '群体符卡\n'
        '出牌阶段，对除你以外的所有其他角色使用，目标角色需依次打出一张|G弹幕|r，否则该角色受到1点伤害。\n\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        return (True, '一只鬼，两只鬼，三只鬼……')

    def sound_effect(self, act):
        return 'thb-cv-card_demonparade'


@ui_meta(definition.FeastCard)
class FeastCard:
    # action_stage meta
    image = 'thb-card-feast'
    name = '宴会'
    description = (
        '|R宴会|r\n\n'
        '群体符卡\n'
        '出牌阶段，对所有角色使用。已受伤的角色回复一点体力，未受伤的角色获得|B喝醉|r状态。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        return (True, '开宴啦~~')

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-card_feast1',
            'thb-cv-card_feast2',
            'thb-cv-card_feast3',
        ])


@ui_meta(definition.HarvestCard)
class HarvestCard:
    # action_stage meta
    image = 'thb-card-harvest'
    name = '五谷丰登'
    description = (
        '|R五谷丰登|r\n\n'
        '群体符卡\n'
        '出牌阶段，对所有角色使用，你从牌堆顶亮出等同于现存角色数量的牌，目标角色依次选择并获得这些牌中的一张。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        return (True, '麻薯会有的，节操是没有的！')

    def sound_effect(self, act):
        return 'thb-cv-card_harvest'


@ui_meta(spellcard.HarvestEffect)
class HarvestEffect:
    def effect_string(self, act):
        if not act.succeeded: return None
        tgt = act.target
        c = act.card
        return '|G【%s】|r获得了|G%s|r' % (
            tgt.ui_meta.name,
            card_desc(c),
        )


@ui_meta(definition.DollControlCard)
class DollControlCard:
    # action_stage meta
    name = '人形操控'
    image = 'thb-card-dollcontrol'
    description = (
        '|R人形操控|r\n\n'
        '出牌阶段，对装备区内有武器牌的一名其他角色使用，令其选择一项：对其攻击范围内一名由你指定的角色使用一张【弹幕】，或将武器交给你。\n\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )
    custom_ray = True

    def is_action_valid(self, g, cl, tl):
        n = len(tl)
        if n == 0:
            return (False, '请选择被控者')

        if tl[0] is g.me:
            return (False, '你不可以控制你自己')

        if all(e.equipment_category != 'weapon' for e in tl[0].equips):
            return (False, '被控者没有武器！')

        if n == 1:
            return (False, '请选择被控者的攻击目标')
        elif n == 2:
            from thb.actions import LaunchCard
            from thb.cards.definition import AttackCard
            c = AttackCard()
            lc = LaunchCard(tl[0], [tl[1]], c)
            if not lc.can_fire():
                return (False, '被控者无法向目标出【弹幕】！')
            return (True, '乖，听话！')

    def sound_effect(self, act):
        return 'thb-cv-card_dollcontrol'


@ui_meta(spellcard.DollControl)
class DollControl:
    # choose card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '那好吧…')
        else:
            return (False, '请出【弹幕】（否则你的武器会被拿走）')

    def ray(self, act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]


@ui_meta(definition.DonationBoxCard)
class DonationBoxCard:
    # action_stage meta
    name = '赛钱箱'
    image = 'thb-card-donationbox'
    description = (
        '|R赛钱箱|r\n\n'
        '非延时符卡\n'
        '出牌阶段，对至多两名其他角色使用，目标角色需将自己的一张牌置入你的明牌区。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    def is_action_valid(self, g, cl, tl):
        n = len(tl)
        if not n:
            return (False, '请选择1-2名玩家')

        for t in tl:
            if not (t.cards or t.showncards or t.equips):
                return (False, '目标没有可以给你的牌')

        return (True, '纳奉！纳奉！')

    def sound_effect(self, act):
        return 'thb-cv-card_donationbox'


@ui_meta(spellcard.DonationBoxEffect)
class DonationBoxEffect:
    # choose card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '这是抢劫啊！')
        else:
            return (False, '请选择一张牌（否则会随机选择一张）')
