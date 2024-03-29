# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import itertools
import random

# -- third party --
# -- own --
from thb.cards import definition, spellcard
from thb.cards.base import PhysicalCard
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(definition.DemolitionCard)
class DemolitionCard:
    # action_stage meta
    name = '城管执法'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '出牌阶段，对一名其他角色使用，弃置其区域内的一张牌。'
    )

    def is_action_valid(self, c, tl):
        if not tl:
            return (False, '请选择拆除目标')

        tgt = tl[0]
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

        # This could happen when:
        # 1. Parsee uses Envy, recycled a diamond card
        # 2. The card is an equipment weared by Alice
        # 3. Alice fires DollBlast, drops the very same card
        # 4. Sometime here, cards are shuffled
        # 5. Demolition now holds a ShreddedCard
        if not isinstance(act.card, PhysicalCard):
            return None

        return f'{N.char(act.source)}卸掉了{N.char(act.target)}的{N.card(act.card)}。'


@ui_meta(definition.RejectCard)
class RejectCard:
    # action_stage meta
    name = '好人卡'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '一张符卡对一名目标角色生效前，你可以使用此牌来抵消该符卡对其目标角色产生的效果。'
    )

    def is_action_valid(self, c, tl):
        return (False, '你不能主动使用好人卡')

    def effect_string(self, act):
        return f'{N.char(act.source)}为{N.char(act.target)}受到的{N.card(act.force_action.target_act.associated_card)}使用了{N.card(act.card)}。'

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
    def choose_card_text(self, act, cards):
        c = act.target_act.associated_card
        s = f'{N.char(act.target_act.target)}受到的{N.card(c)}'

        if act.cond(cards):
            return True, f'对不起，你是一个好人({s})'
        else:
            return False, f'请选择一张好人卡（{s})'


@ui_meta(definition.SealingArrayCard)
class SealingArrayCard:
    # action_stage meta
    name = '封魔阵'
    illustrator = '霏茶'
    cv = 'shourei小N'
    tag = 'sealarray'
    description = (
        '出牌阶段，对一名其他角色使用，将此牌横置于该角色的判定区内。该角色的判定阶段，需进行一次判定然后弃置此牌。若判定结果不为红桃，跳过其出牌阶段。'
    )

    def is_action_valid(self, c, tl):
        if len(tl) != 1:
            return (False, '请选择封魔阵的目标')
        t = tl[0]
        if self.me is t:
            return (False, '你不能跟自己过不去啊！')

        return (True, '画个圈圈诅咒你！')

    def sound_effect(self, act):
        return 'thb-cv-card_sealarray'


@ui_meta(spellcard.SealingArray)
class SealingArray:
    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return f'{N.char(tgt)}被困在了封魔阵中。'
        else:
            return f'封魔阵没有布置完善，{N.char(tgt)}侥幸逃了出来！'


@ui_meta(definition.FrozenFrogCard)
class FrozenFrogCard:
    # action_stage meta
    name = '冻青蛙'
    illustrator = '霏茶'
    cv = 'shourei小N'
    tag = 'frozenfrog'
    description = (
        '出牌阶段，对一名其他角色使用，将此牌横置于该角色的判定区内。该角色的判定阶段，需进行一次判定然后弃置此牌。若判定结果不为黑桃，跳过其摸牌阶段。'
    )

    def is_action_valid(self, c, tl):
        if len(tl) != 1:
            return (False, '请选择冻青蛙的目标')
        t = tl[0]
        if self.me is t:
            return (False, '你不能跟自己过不去啊！')

        return (True, '伸手党什么的，冻住就好了！')

    def sound_effect(self, act):
        return 'thb-cv-card_frozenfrog'


@ui_meta(spellcard.FrozenFrog)
class FrozenFrog:
    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return f'{N.char(tgt)}被冻住了……'
        else:
            return f'幻想乡今天大晴，{N.char(tgt)}没有被冻住~'


@ui_meta(definition.NazrinRodCard)
class NazrinRodCard:
    # action_stage meta
    name = '寻龙尺'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '出牌阶段使用，摸两张牌。'
    )

    def is_action_valid(self, c, tl):
        return (True, '看看能找到什么好东西~')

    def sound_effect(self, act):
        return 'thb-cv-card_nazrinrod'


@ui_meta(definition.SinsackCard)
class SinsackCard:
    # action_stage meta
    name = '罪袋'
    illustrator = '霏茶'
    cv = 'VV/大白'
    tag = 'sinsack'
    description = (
        '出牌阶段，对你使用，将此牌横置于你的判定区内。判定区内有此牌的角色的判定阶段，需进行一次判定：'
        '<style=Desc.Li>若判定结果为♠1-8，则目标角色受到3点无来源伤害，然后将其置入弃牌堆。</style>'
        '<style=Desc.Li>若判定结果不在此范围，则将其移动到下家的判定区内。</style>'
        '<style=Desc.Li>判定开始前,你可以使用<style=B>好人卡</style>抵消该符卡的效果,并将该<style=Card.Name>罪袋</style>直接传递给下家。</style>'
    )

    def is_action_valid(self, c, tl):
        return (True, '别来找我！')

    def sound_effect(self, act):
        return 'thb-cv-card_sinsack'


@ui_meta(spellcard.Sinsack)
class Sinsack:
    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return f'罪袋终于找到了机会，将{N.char(tgt)}推倒了…'


@ui_meta(spellcard.SinsackDamage)
class SinsackDamage:
    def sound_effect(self, act):
        return 'thb-cv-card_sinsack_effect'


@ui_meta(definition.YukariDimensionCard)
class YukariDimensionCard:
    # action_stage meta
    name = '隙间'
    illustrator = '霏茶'
    cv = 'VV'

    description = (
        '出牌阶段，对距离为1的一名其他角色使用，获得其区域内的一张牌。'
    )

    def is_action_valid(self, c, tl):
        if not tl:
            return (False, '请选择目标')

        target = tl[0]
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
            return f'{N.char(src)}透过隙间拿走了{N.char(tgt)}的{N.card(act.card)}。'


@ui_meta(definition.DuelCard)
class DuelCard:
    # action_stage meta
    name = '弹幕战'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '出牌阶段，对一名其他角色使用，由目标角色开始，轮流打出一张<style=Card.Name>弹幕</style>。首先不打出<style=Card.Name>弹幕</style>的一方受到另一方造成的1点伤害。'
    )

    def is_action_valid(self, c, tl):
        if not tl:
            return (False, '请选择弹幕战的目标')

        return (True, '来，战个痛快！')

    def sound_effect(self, act):
        return 'thb-cv-card_duel'


@ui_meta(definition.MapCannonCard)
class MapCannonCard:
    name = '地图炮'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '出牌阶段，对除你以外的所有其他角色使用，目标角色需依次打出一张<style=Card.Name>擦弹</style>，否则该角色受到1点伤害。'
    )

    def is_action_valid(self, c, tl):
        return (True, '一个都不能跑！')

    def sound_effect(self, act):
        return 'thb-cv-card_mapcannon'


@ui_meta(definition.DemonParadeCard)
class DemonParadeCard:
    name = '百鬼夜行'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '出牌阶段，对除你以外的所有其他角色使用，目标角色需依次打出一张<style=Card.Name>弹幕</style>，否则该角色受到1点伤害。'
    )

    def is_action_valid(self, c, tl):
        return (True, '一只鬼，两只鬼，三只鬼……')

    def sound_effect(self, act):
        return 'thb-cv-card_demonparade'


@ui_meta(definition.FeastCard)
class FeastCard:
    # action_stage meta
    name = '宴会'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '出牌阶段，对所有角色使用。已受伤的角色回复一点体力，未受伤的角色获得<style=B>喝醉</style>状态。'
    )

    def is_action_valid(self, c, tl):
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
    name = '五谷丰登'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '出牌阶段，对所有角色使用，你从牌堆顶亮出等同于现存角色数量的牌，目标角色依次选择并获得这些牌中的一张。'
    )

    def is_action_valid(self, c, tl):
        return (True, '麻薯会有的，节操是没有的！')

    def sound_effect(self, act):
        return 'thb-cv-card_harvest'


@ui_meta(spellcard.Harvest)
class Harvest:

    def detach_cards_tip(self, trans, cards) -> str:
        return ''

    def drop_cards_tip(self, trans) -> str:
        return '<style=Skill.Name>五谷丰登</style>剩余'


@ui_meta(spellcard.HarvestEffect)
class HarvestEffect:
    def effect_string(self, act):
        if not act.succeeded: return None
        return f'{N.char(act.target)}获得了{N.card(act.card)}。'


@ui_meta(definition.DollControlCard)
class DollControlCard:
    # action_stage meta
    name = '人形操控'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '出牌阶段，对装备区内有武器牌的一名其他角色使用，令其选择一项：对其攻击范围内一名由你指定的角色使用一张<style=Card.Name>弹幕</style>，或将武器交给你。'
    )
    custom_ray = True

    def is_action_valid(self, c, tl):
        n = len(tl)
        if n == 0:
            return (False, '请选择被控者')

        if tl[0] is self.me:
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
                return (False, '被控者无法向目标使用<style=Card.Name>弹幕</style>！')
            return (True, '乖，听话！')

    def sound_effect(self, act):
        return 'thb-cv-card_dollcontrol'


@ui_meta(spellcard.DollControl)
class DollControl:
    # choose card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '那好吧…')
        else:
            return (False, '请使用<style=Card.Name>弹幕</style>（否则你的武器会被拿走）')

    def ray(self, act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]


@ui_meta(definition.DonationBoxCard)
class DonationBoxCard:
    # action_stage meta
    name = '赛钱箱'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '出牌阶段，对至多两名其他角色使用，目标角色需将自己的一张牌置入你的明牌区。'
    )

    def is_action_valid(self, c, tl):
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
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '这是抢劫啊！')
        else:
            return (False, '请选择一张牌（否则会随机选择一张）')
