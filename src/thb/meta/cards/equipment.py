# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Optional
import random

# -- third party --
# -- own --
from thb import actions
from thb.actions import ttags
from thb.cards import basic, definition, equipment, definition as D
from thb.cards.base import Card
from thb.meta.common import ui_meta, N
from utils.misc import BatchList


# -- code --
def equip_iav(self, c, tl):
    return (True, '配上好装备，不再掉节操！')


def suppress_launch_card_effect_string(self, act):
    return None


@ui_meta(equipment.WearEquipmentAction)
class WearEquipmentAction:
    choose_option_prompt = '你希望重铸这张牌么？'
    choose_option_buttons = (('重铸', True), ('装备', False))

    def effect_string(self, act):
        if act.action == 'wear':
            c = act.associated_card
            return f'{N.char(act.target)}装备了{N.card(c)}。'


@ui_meta(equipment.ReforgeWeapon)
class ReforgeWeapon:
    def effect_string(self, act):
        return f'{N.char(act.target)}重铸了{N.card(act.card)}。'


@ui_meta(definition.OpticalCloakCard)
class OpticalCloakCard:
    # action_stage meta
    name = '光学迷彩'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '装备后：当你需要使用或打出<style=Card.Name>擦弹</style>时，可以进行一次判定，若结果为红，视为你使用或打出了一张<style=Card.Name>擦弹</style>。'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.OpticalCloakSkill)
class OpticalCloakSkill:
    # Skill
    name = '光学迷彩'

    def sound_effect(self, act):
        return 'thb-cv-card_opticalcloak'

    def effect_string(self, act):
        return definition.GrazeCard.ui_meta.effect_string(act)


@ui_meta(equipment.OpticalCloakHandler)
class OpticalCloakHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Card.Name>光学迷彩</style>吗？'


@ui_meta(equipment.OpticalCloak)
class OpticalCloak:
    fatetell_display_name = '光学迷彩'

    def effect_string_before(self, act):
        return f'{N.char(act.target)}祭起了{N.card(D.OpticalCloakCard)}…'

    def effect_string(self, act):
        if act.succeeded:
            return '效果拔群！'
        else:
            return '但是被看穿了…'


@ui_meta(definition.MomijiShieldCard)
class MomijiShieldCard:
    # action_stage meta
    name = '天狗盾'
    illustrator = '霏茶'
    cv = ''
    description = (
        '装备后：黑色<style=Card.Name>弹幕</style>对你无效。\n\n'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.MomijiShieldSkill)
class MomijiShieldSkill:
    # Skill
    name = '天狗盾'


@ui_meta(equipment.MomijiShield)
class MomijiShield:
    def effect_string(self, act):
        return '被{N.char(D.MomijiShieldCard)}挡下了…'

    def sound_effect(self, act):
        return 'thb-cv-card_momijishield'


ufo_desc = (
    'UFO用来改变自己与其他角色之间的距离。'
    '<style=Desc.Li>红色UFO为进攻用，当你计算和其他角色的距离时，在原有的基础上减少相应距离。两名角色之间的距离至少为1。</style>'
    '<style=Desc.Li>绿色UFO为防守用，当其他角色计算和你的距离时，在原有的基础上增加相应距离。</style>'
    '<style=Desc.Li>你可以同时装备两种UFO。</style>'
)


@ui_meta(definition.GreenUFOCard)
class GreenUFOCard:
    # action_stage meta
    name = '绿色UFO'
    description = ufo_desc
    illustrator = '霏茶'
    cv = ''

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.GreenUFOSkill)
class GreenUFOSkill:
    # Skill
    name = '绿色UFO'


@ui_meta(definition.RedUFOCard)
class RedUFOCard:
    # action_stage meta
    name = '红色UFO'
    illustrator = '霏茶'
    cv = ''
    description = ufo_desc

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.RedUFOSkill)
class RedUFOSkill:
    # Skill
    name = '红色UFO'


@ui_meta(definition.RoukankenCard)
class RoukankenCard:
    # action_stage meta
    name = '楼观剑'
    illustrator = '霏茶'
    cv = ''
    description = (
        '攻击范围3，装备后：你使用的<style=Card.Name>弹幕</style>无视防具。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.RoukankenSkill)
class RoukankenSkill:
    # Skill
    name = '楼观剑'


@ui_meta(equipment.Roukanken)
class Roukanken:
    def effect_string_apply(self, act):
        return '没有什么防具是<style=Card.Name>楼观剑</style>斩不断的！'

    def sound_effect(self, act):
        return 'thb-cv-card_roukanken'


@ui_meta(definition.ElementalReactorCard)
class ElementalReactorCard:
    # action_stage meta
    name = '八卦炉'
    illustrator = '霏茶'
    cv = ''
    description = (
        '攻击范围1，装备后：出牌阶段你使用<style=Card.Name>弹幕</style>时不消耗干劲。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.ElementalReactorSkill)
class ElementalReactorSkill:
    # Skill
    name = '八卦炉'


@ui_meta(definition.UmbrellaCard)
class UmbrellaCard:
    # action_stage meta
    name = '阳伞'
    illustrator = '霏茶'
    cv = ''
    description = (
        '符卡效果造成的伤害对你无效。'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.UmbrellaSkill)
class UmbrellaSkill:
    # Skill
    name = '紫的阳伞'


@ui_meta(equipment.UmbrellaEffect)
class UmbrellaEffect:
    def effect_string_before(self, act):
        a = act.action
        dmg = act.damage_act
        card = getattr(a, 'associated_card', None)
        if card and card.associated_action and isinstance(a, card.associated_action):
            # Some skills changes action
            s = N.card(card.__class__)
        else:
            s = ''

        return f'{N.char(dmg.target)}受到的{s}效果被<style=Card.Name>阳伞</style>挡下了…'

    def sound_effect(self, act):
        return 'thb-cv-card_umbrella'


@ui_meta(definition.GungnirCard)
class GungnirCard:
    # action_stage meta
    name = '冈格尼尔'
    illustrator = '霏茶'
    cv = ''
    description = (
        '攻击范围3，装备后：你可以将两张手牌当<style=Card.Name>弹幕</style>使用或打出。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.GungnirSkill)
class GungnirSkill:
    # Skill
    name = '冈格尼尔'

    def clickable(self):
        me = self.me
        return self.accept_cards([equipment.GungnirSkill(me)])

    def is_complete(self, skill):
        me = self.me
        assert skill.is_card(equipment.GungnirSkill)
        acards = skill.associated_cards
        if len(acards) != 2:
            return (False, '请选择2张手牌！')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in acards):
            return (False, '只能使用手牌发动！')
        return (True, '反正这条也看不到，偷个懒~~~')

    def is_action_valid(self, sk, tl):
        assert sk.is_card(equipment.GungnirSkill)
        rst, reason = self.is_complete(sk)
        if not rst:
            return (rst, reason)
        else:
            return definition.AttackCard().ui_meta.is_action_valid(sk, tl)

    def effect_string(self, act):
        # for LaunchCard.effect_string
        source = act.source
        target = act.target
        return f'{N.char(source)}发动了<style=Card.Name>冈格尼尔</style>之枪，将两张牌当作<style=Card.Name>弹幕</style>对{N.char(target)}使用。'

    def sound_effect(self, act):
        return definition.AttackCard.ui_meta.sound_effect(act)


@ui_meta(definition.ScarletRhapsodyCard)
class ScarletRhapsodyCard:
    # action_stage meta
    name = '绯想之剑'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '攻击范围4，装备后：当你使用的<style=Card.Name>弹幕</style>是你的最后一张手牌时，你可以为此<style=Card.Name>弹幕</style>指定至多三名目标。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.ScarletRhapsodySkill)
class ScarletRhapsodySkill:
    # Skill
    name = '绯想之剑'

    def clickable(self):
        g = self.game
        me = self.me
        try:
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return act.target is me

        except IndexError:
            pass

        return False

    def is_action_valid(self, sk, tl):
        assert sk.is_card(equipment.ScarletRhapsodySkill)
        if not sk.check():
            return (False, '请选择你的最后一张<style=Card.Name>弹幕</style>！')
        else:
            if not tl:
                return (False, '请选择弹幕的目标（最多可以选择3名玩家）')

            if self.me in tl:
                return (True, '您真的要自残么？！')
            else:
                return (True, '全人类的绯想天！')

    def effect_string(self, act: actions.LaunchCard) -> Optional[str]:
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        tl = BatchList(act.target_list)

        return f'全人类的绯想天，当然不能只打一个！于是{N.char(src)}选了{N.char(tl)}一共{len(tl)}个目标！'

    def sound_effect(self, act):
        return 'thb-cv-card_srs'


@ui_meta(definition.RepentanceStickCard)
class RepentanceStickCard:
    # action_stage meta
    name = '悔悟棒'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '攻击范围2，装备后：当你使用<style=Card.Name>弹幕</style>造成伤害时，你可以防止此伤害，改为依次弃置目标角色区域内的两张牌。'
        '<style=Desc.Li>区域内的牌包括手牌，装备区的牌和判定区的牌。</style>'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.RepentanceStickSkill)
class RepentanceStickSkill:
    # Skill
    name = '悔悟棒'


@ui_meta(equipment.RepentanceStickHandler)
class RepentanceStickHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Card.Name>悔悟棒</style>吗？'


@ui_meta(equipment.RepentanceStick)
class RepentanceStick:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}用<style=Card.Name>悔悟棒</style>狠狠地敲了{N.char(act.target)}一通…'

    def effect_string(self, act: equipment.RepentanceStick) -> str:
        cl = BatchList[Card](act.cards)
        return f"又抢过{N.char(act.target)}的{N.card(cl, '和')}扔了出去！"

    def sound_effect(self, act):
        return 'thb-cv-card_repentancestick'


@ui_meta(definition.IbukiGourdCard)
class IbukiGourdCard:
    # action_stage meta
    name = '伊吹瓢'
    illustrator = '霏茶'
    cv = ''
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string

    description = (
        '装备后立即获得<style=B>喝醉</style>状态。并且，若你在出牌阶段没有造成过伤害，在回合结束阶段获得<style=B>喝醉</style>状态。'
    )


@ui_meta(equipment.IbukiGourdSkill)
class IbukiGourdSkill:
    # Skill
    name = '伊吹瓢'


@ui_meta(definition.HouraiJewelCard)
class HouraiJewelCard:
    # action_stage meta
    name = '蓬莱玉枝'
    illustrator = '霏茶'
    cv = ''
    description = (
        '攻击范围1。装备后，你使用的<style=Card.Name>弹幕</style>时，可以将弹幕的效果转化成如下的符卡效果：造成1点伤害。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.HouraiJewelSkill)
class HouraiJewelSkill:
    # Skill
    name = '蓬莱玉枝'


@ui_meta(equipment.HouraiJewelHandler)
class HouraiJewelHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Card.Name>蓬莱玉枝</style>吗？'


@ui_meta(equipment.HouraiJewelAttack)
class HouraiJewelAttack:
    def effect_string_apply(self, act):
        return f'{N.char(act.source)}发动了<style=Card.Name>蓬莱玉枝</style>，包裹着魔法核心的弹幕冲向了{N.char(act.target)}！'


@ui_meta(definition.MaidenCostumeCard)
class MaidenCostumeCard:
    # action_stage meta
    name = '巫女服'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '装备后：当你成为一张符卡的目标时，你可以进行一次判定：若判定牌点数为9到K，则视为你使用了一张<style=Card.Name>好人卡</style>。'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.MaidenCostume)
class MaidenCostume:
    # Skill
    name = '巫女服'

    def sound_effect(self, act):
        return 'thb-cv-card_maidencostume'


@ui_meta(equipment.MaidenCostumeHandler)
class MaidenCostumeHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Card.Name>巫女服</style>吗？'


@ui_meta(equipment.MaidenCostumeAction)
class MaidenCostumeAction:
    fatetell_display_name = '巫女服'

    def effect_string_before(self, act):
        return f'{N.char(act.source)}穿了<style=Card.Name>巫女服</style>，春度爆表，不怕符卡！'

    def effect_string(self, act):
        if not act.succeeded:
            return f'好像{N.char(act.source)}的春度还是不够用…'


@ui_meta(definition.HakuroukenCard)
class HakuroukenCard:
    # action_stage meta
    name = '白楼剑'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '攻击范围2，装备后：当你使用的草花色<style=Card.Name>弹幕</style>指定一名目标角色后，你可以令其选择一项：'
        '<style=Desc.Li>弃置一张手牌。</style>'
        '<style=Desc.Li>令你摸一张牌。</style>'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.HakuroukenSkill)
class HakuroukenSkill:
    # Skill
    name = '白楼剑'


@ui_meta(equipment.Hakurouken)
class Hakurouken:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '弃置这张牌')
        else:
            return (False, '请弃掉一张牌（否则对方摸一张牌）')

    def effect_string_before(self, act):
        return f'{N.char(act.source)}祭起了<style=Card.Name>白楼剑</style>，试图斩断{N.char(act.target)}的迷惘！'

    def effect_string(self, act):
        if act.peer_action == 'drop':
            return f'{N.char(act.target)}弃置了一张牌。'
        else:
            return None  # DrawCards has it's own prompt

    def sound_effect(self, act):
        return 'thb-cv-card_hakurouken'


@ui_meta(equipment.HakuroukenHandler)
class HakuroukenHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Card.Name>白楼剑</style>吗？'


@ui_meta(definition.AyaRoundfanCard)
class AyaRoundfanCard:
    # action_stage meta
    name = '团扇'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '攻击距离5，装备后：当你使用的<style=Card.Name>弹幕</style>对目标角色造成伤害后，你可以弃置一张手牌，然后弃置其装备区里的一张牌。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.AyaRoundfanSkill)
class AyaRoundfanSkill:
    # Skill
    name = '团扇'


@ui_meta(equipment.AyaRoundfanHandler)
class AyaRoundfanHandler:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '这种妨碍拍摄的东西，统统脱掉！')
        else:
            return (False, '请弃掉一张手牌发动团扇（否则不发动）')


@ui_meta(equipment.AyaRoundfan)
class AyaRoundfan:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}觉得手中的<style=Card.Name>团扇</style>用起来好顺手，便加大力度试了试…'

    def effect_string(self, act):
        return f'于是{N.char(act.target)}的{N.card(act.card)}就飞了出去！'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-card_roundfan1',
            'thb-cv-card_roundfan2',
        ])


@ui_meta(definition.NenshaPhoneCard)
class NenshaPhoneCard:
    # action_stage meta
    name = '念写机'
    illustrator = '霏茶'
    cv = ''
    description = (
        '攻击距离4，装备后：当你使用的<style=Card.Name>弹幕</style>对目标角色造成伤害后，可以将其两张手牌置入明牌区。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.NenshaPhoneSkill)
class NenshaPhoneSkill:
    # Skill
    name = '念写机'


@ui_meta(equipment.NenshaPhoneHandler)
class NenshaPhoneHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Card.Name>念写机</style>吗？'


@ui_meta(equipment.NenshaPhone)
class NenshaPhone:
    def effect_string(self, act):
        return f'{N.char(act.source)}表示，将{N.char(act.target)}推倒后拍摄胖次，是记者的自我修养中不可或缺的一部分。'

    def sound_effect(self, act):
        return 'thb-cv-card_nenshaphone'


@ui_meta(definition.LaevateinCard)
class LaevateinCard:
    # action_stage meta
    name = '莱瓦汀'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '攻击距离3，装备后：当你使用的<style=Card.Name>弹幕</style>被目标角色使用的<style=Card.Name>擦弹</style>抵消时，你可以弃置两张牌，令此<style=Card.Name>弹幕</style>依然生效。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.LaevateinSkill)
class LaevateinSkill:
    # Skill
    name = '莱瓦汀'


@ui_meta(equipment.LaevateinHandler)
class LaevateinHandler:
    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '灭世之炎岂能轻易闪过！')
        else:
            return (False, '请弃掉两张牌发动莱瓦汀（否则不发动）')


@ui_meta(equipment.Laevatein)
class Laevatein:
    def effect_string_before(self, act):
        return '<style=Card.Name>莱瓦汀</style>的灭世之炎岂能轻易闪过！'

    def sound_effect(self, act):
        return 'thb-cv-card_laevatein'


@ui_meta(definition.DeathSickleCard)
class DeathSickleCard:
    # action_stage meta
    name = '死神之镰'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '攻击范围2，装备后：当你使用的<style=Card.Name>弹幕</style>对目标角色造成伤害时，若其没有手牌，此伤害+1。'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.DeathSickleSkill)
class DeathSickleSkill:
    # Skill
    name = '死神之镰'


@ui_meta(equipment.DeathSickle)
class DeathSickle:
    def effect_string(self, act):
        return f'{N.char(act.source)}看到{N.char(act.target)}一副丧家犬的模样，手中的<style=Card.Name>死神之镰</style>不自觉地一狠…'

    def sound_effect(self, act):
        return 'thb-cv-card_deathsickle'


@ui_meta(definition.KeystoneCard)
class KeystoneCard:
    # action_stage meta
    name = '要石'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '特殊的绿色UFO装备，距离+1。'
        '装备后跳过<style=Card.Name>罪袋</style>对你的结算。'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.KeystoneSkill)
class KeystoneSkill:
    # Skill
    name = '要石'


@ui_meta(equipment.Keystone)
class Keystone:
    def effect_string(self, act):
        return f'{N.char(act.target)}站在<style=Card.Name>要石</style>上，照着<style=Card.Name>罪袋</style>的脸一脚踹了下去！'

    def sound_effect(self, act):
        return 'thb-cv-card_keystone'


@ui_meta(definition.WitchBroomCard)
class WitchBroomCard:
    # action_stage meta
    name = '魔女扫把'
    illustrator = '霏茶'
    cv = ''
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string
    description = (
        '特殊的红色UFO装备，距离-2。'
    )


# @ui_meta(equipment.WitchBroomSkill)
# class WitchBroomSkill:
#     # Skill
#     pass


@ui_meta(definition.YinYangOrbCard)
class YinYangOrbCard:
    # action_stage meta
    name = '阴阳玉'
    illustrator = '霏茶'
    cv = ''
    description = (
        '在你的判定牌生效前，你可以用装备区内的<style=Card.Name>阴阳玉</style>替换之。'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.YinYangOrbSkill)
class YinYangOrbSkill:
    # Skill
    name = '阴阳玉'


@ui_meta(equipment.YinYangOrbHandler)
class YinYangOrbHandler:
    # choose_option
    choose_option_buttons = (('替换', True), ('不替换', False))
    choose_option_prompt = '你要使用<style=Card.Name>阴阳玉</style>替换当前的判定牌吗？'


@ui_meta(equipment.YinYangOrb)
class YinYangOrb:
    def effect_string(self, act):
        return f'{N.char(act.target)}用{N.card(act.card)}替换了她的判定牌。'


@ui_meta(definition.SuwakoHatCard)
class SuwakoHatCard:
    # action_stage meta
    name = '青蛙帽'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '装备后手牌上限+2。'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.SuwakoHatSkill)
class SuwakoHatSkill:
    # Skill
    name = '青蛙帽'


@ui_meta(equipment.SuwakoHatEffect)
class SuwakoHatEffect:
    def sound_effect(self, act):
        return 'thb-cv-card_suwakohat'


@ui_meta(definition.YoumuPhantomCard)
class YoumuPhantomCard:
    # action_stage meta
    name = '半灵'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '装备后增加1点体力上限。当失去装备区里的<style=Card.Name>半灵</style>时，你回复1点体力。'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.YoumuPhantomSkill)
class YoumuPhantomSkill:
    # Skill
    name = '半灵'


@ui_meta(equipment.YoumuPhantomHeal)
class YoumuPhantomHeal:
    def sound_effect(self, act):
        return 'thb-cv-card_phantom'


@ui_meta(definition.IceWingCard)
class IceWingCard:
    # action_stage meta
    name = '⑨的翅膀'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '特殊的红色UFO装备，距离-1。'
        '装备后，<style=Card.Name>封魔阵</style>和<style=Card.Name>冻青蛙</style>对你无效。'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.IceWingSkill)
class IceWingSkill:
    # Skill
    name = '⑨的翅膀'


@ui_meta(equipment.IceWing)
class IceWing:
    def effect_string(self, act):
        c = act.action.associated_card
        return f'{N.char(act.target)}借着<style=Card.Name>⑨的翅膀</style>飞了出来，{N.card(c)}没起到什么作用。'

    def sound_effect(self, act):
        tgt = act.target
        if ttags(tgt)['__icewing_se']:
            return None

        ttags(tgt)['__icewing_se'] = True
        return 'thb-cv-card_icewing'


@ui_meta(definition.GrimoireCard)
class GrimoireCard:
    # action_stage meta
    name = '魔导书'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '攻击距离1，装备后，你可以消耗一点干劲并将一张牌按照以下规则使用：'
        '<style=Desc.Li>黑桃♠视为<style=Card.Name>百鬼夜行</style>。</style>'
        '<style=Desc.Li>红桃♥视为<style=Card.Name>宴会</style>。</style>'
        '<style=Desc.Li>梅花♣视为<style=Card.Name>地图炮</style>。</style>'
        '<style=Desc.Li>方片♦视为<style=Card.Name>五谷丰登</style>。</style>'
        '<style=Desc.Attention>出牌阶段你可以消耗1点干劲重铸手牌中的武器</style>'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.GrimoireSkill)
class GrimoireSkill:
    # Skill
    name = '魔导书'

    def clickable(self):
        g = self.game
        me = self.me
        if ttags(me)['grimoire_tag']:
            return False

        if not self.my_turn():
            return False

        if ttags(me)['vitality'] > 0:
            if not basic.AttackCardVitalityHandler.is_disabled(me):
                return True

        if me.has_skill(equipment.ElementalReactorSkill):
            return True

        return False

    def is_action_valid(self, sk, tl):
        assert sk.is_card(equipment.GrimoireSkill)
        acards = sk.associated_cards
        if not (len(acards)) == 1:
            return (False, '请选择一张牌')
        else:
            cls = sk.lookup_tbl[acards[0].suit]
            return (True, f'发动{N.card(cls)}')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        tc = card.lookup_tbl[card.associated_cards[0].suit]
        return f'{N.char(source)}抓起一张牌放入<style=Card.Name>魔导书</style>，念动咒语，发动了{N.card(tc)}。'

    def sound_effect(self, act):
        return 'thb-cv-card_grimoire'


@ui_meta(equipment.SinsackHatAction)
class SinsackHatAction:
    fatetell_display_name = '头套'

    def effect_string_before(self, act):
        return f'看着戴着<style=Card.Name>头套</style>的{N.char(act.target)}，真正的的罪袋们都兴奋了起来！'


@ui_meta(equipment.SinsackHat)
class SinsackHat:
    # Skill
    name = '头套'


@ui_meta(definition.SinsackHatCard)
class SinsackHatCard:
    # action_stage meta
    name = '头套'
    illustrator = '霏茶'
    cv = '大白'
    description = (
        '对距离2以内的一名角色使用。'
        '装备<style=Card.Name>头套</style>的角色需在判定阶段后进行一次判定，若为♠1-8，则该角色受到2点伤害，并且将<style=Card.Name>头套</style>收入手牌。'
    )

    def is_action_valid(self, c, tl):
        if not tl:
            return (False, '请选择目标')
        t = tl[0]
        if self.me is t:
            return (True, '真的要自己戴上吗？')
        return (True, '是这样的，这个不是胖次……不不，真的没有胖次')

    effect_string = suppress_launch_card_effect_string
