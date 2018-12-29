# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Optional
import random

# -- third party --
# -- own --
from thb import actions
from thb.cards.base import Card
from thb.actions import ttags
from thb.cards import definition, equipment
from thb.meta.common import card_desc, passive_clickable, passive_is_action_valid, ui_meta
from utils.misc import BatchList


# -- code --


def equip_iav(self, g, cl, tl):
    return (True, '配上好装备，不再掉节操！')


def suppress_launch_card_effect_string(self, act):
    return None


@ui_meta(equipment.WearEquipmentAction)
class WearEquipmentAction:

    def effect_string(self, act):
        return '|G【%s】|r装备了%s' % (
            act.target.ui_meta.name,
            card_desc(act.associated_card),
        )


@ui_meta(equipment.WeaponReforgeHandler)
class WeaponReforgeHandler:
    choose_option_prompt = '你希望重铸这张牌么？'
    choose_option_buttons = (('重铸', True), ('装备', False))


@ui_meta(equipment.ReforgeWeapon)
class ReforgeWeapon:
    def effect_string(self, act):
        return '|G【%s】|r重铸了%s' % (
            act.target.ui_meta.name,
            card_desc(act.card),
        )


@ui_meta(definition.OpticalCloakCard)
class OpticalCloakCard:
    # action_stage meta
    name = '光学迷彩'
    image = 'thb-card-opticalcloak'
    image_small = 'thb-card-small-opticalcloak'
    description = (
        '|R光学迷彩|r\n\n'
        '装备后:当你需要使用或打出|G擦弹|r时，可以进行一次判定，若结果为红，视为你使用或打出了一张|G擦弹|r。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.OpticalCloakSkill)
class OpticalCloakSkill:
    # Skill
    name = '光学迷彩'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    def sound_effect(self, act):
        return 'thb-cv-card_opticalcloak'

    def effect_string(self, act):
        return definition.GrazeCard.ui_meta.effect_string(act)


@ui_meta(equipment.OpticalCloakHandler)
class OpticalCloakHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【光学迷彩】吗？'


@ui_meta(equipment.OpticalCloak)
class OpticalCloak:
    fatetell_display_name = '光学迷彩'

    def effect_string_before(self, act):
        return '|G【%s】|r祭起了|G光学迷彩|r…' % (
            act.target.ui_meta.name,
        )

    def effect_string(self, act):
        if act.succeeded:
            return '效果拔群！'
        else:
            return '但是被看穿了…'


@ui_meta(definition.MomijiShieldCard)
class MomijiShieldCard:
    # action_stage meta
    name = '天狗盾'
    image = 'thb-card-momijishield'
    image_small = 'thb-card-small-momijishield'
    description = (
        '|R天狗盾|r\n\n'
        '装备后：黑色|G弹幕|r对你无效。\n\n'
        '|DB（画师：霏茶）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.MomijiShieldSkill)
class MomijiShieldSkill:
    # Skill
    name = '天狗盾'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.MomijiShield)
class MomijiShield:
    def effect_string(self, act):
        return '被|G天狗盾|r挡下了…'

    def sound_effect(self, act):
        return 'thb-cv-card_momijishield'


ufo_desc = (
    '|R%s|r\n\n'
    'UFO用来改变自己与其他角色之间的距离。\n'
    '|B|R>> |r红色UFO为进攻用，当你计算和其他角色的距离时,在原有的基础上减少相应距离。两名角色之间的距离至少为1。\n'
    '|B|R>> |r绿色UFO为防守用，当其他角色计算和你的距离时,在原有的基础上增加相应距离。\n'
    '|B|R>> |r你可以同时装备两种UFO\n\n'
    '|DB（画师：霏茶）|r'
)


@ui_meta(definition.GreenUFOCard)
class GreenUFOCard:
    # action_stage meta
    name = '绿色UFO'
    image = 'thb-card-greenufo'
    image_small = 'thb-card-small-greenufo'
    description = ufo_desc % name

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.GreenUFOSkill)
class GreenUFOSkill:
    # Skill
    name = '绿色UFO'
    no_display = True
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(definition.RedUFOCard)
class RedUFOCard:
    # action_stage meta
    name = '红色UFO'
    image = 'thb-card-redufo'
    image_small = 'thb-card-small-redufo'
    description = ufo_desc % name

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.RedUFOSkill)
class RedUFOSkill:
    # Skill
    name = '红色UFO'
    no_display = True
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(definition.RoukankenCard)
class RoukankenCard:
    # action_stage meta
    name = '楼观剑'
    image = 'thb-card-roukanken'
    image_small = 'thb-card-small-roukanken'
    description = (
        '|R楼观剑|r\n'
        '\n'
        '攻击范围3，装备后：你使用的|G弹幕|r无视防具。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.RoukankenSkill)
class RoukankenSkill:
    # Skill
    name = '楼观剑'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.Roukanken)
class Roukanken:
    def effect_string_apply(self, act):
        return '没有什么防具是|G楼观剑|r斩不断的！'

    def sound_effect(self, act):
        return 'thb-cv-card_roukanken'


@ui_meta(definition.ElementalReactorCard)
class ElementalReactorCard:
    # action_stage meta
    name = '八卦炉'
    image = 'thb-card-reactor'
    image_small = 'thb-card-small-reactor'
    description = (
        '|R八卦炉|r\n'
        '\n'
        '攻击范围1，装备后：出牌阶段你使用|G弹幕|r时不消耗干劲。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.ElementalReactorSkill)
class ElementalReactorSkill:
    # Skill
    name = '八卦炉'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(definition.UmbrellaCard)
class UmbrellaCard:
    # action_stage meta
    name = '阳伞'
    image = 'thb-card-umbrella'
    image_small = 'thb-card-small-umbrella'
    description = (
        '|R阳伞|r\n\n'
        '装备后：符卡效果造成的伤害对你无效。\n\n'
        '|DB（画师：霏茶）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.UmbrellaSkill)
class UmbrellaSkill:
    # Skill
    name = '紫的阳伞'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.UmbrellaEffect)
class UmbrellaEffect:
    def effect_string_before(self, act):
        a = act.action
        dmg = act.damage_act
        card = getattr(a, 'associated_card', None)
        if card and card.associated_action and isinstance(a, card.associated_action):
            # Some skills changes action
            s = '|G%s|r' % card.ui_meta.name
        else:
            s = ''

        return '|G【%s】|r受到的%s效果被|G阳伞|r挡下了' % (
            dmg.target.ui_meta.name, s,
        )

    def sound_effect(self, act):
        return 'thb-cv-card_umbrella'


@ui_meta(definition.GungnirCard)
class GungnirCard:
    # action_stage meta
    name = '冈格尼尔'
    image = 'thb-card-gungnir'
    image_small = 'thb-card-small-gungnir'
    description = (
        '|R冈格尼尔|r\n'
        '\n'
        '攻击范围3，装备后：你可以将两张手牌当|G弹幕|r使用或打出。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.GungnirSkill)
class GungnirSkill:
    # Skill
    name = '冈格尼尔'

    def clickable(self, g):
        try:
            act = g.hybrid_stack[-1]
            if act.cond([equipment.GungnirSkill(g.me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(self, g, skill):
        me = g.me
        assert skill.is_card(equipment.GungnirSkill)
        acards = skill.associated_cards
        if len(acards) != 2:
            return (False, '请选择2张手牌！')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in acards):
            return (False, '只能使用手牌发动！')
        return (True, '反正这条也看不到，偷个懒~~~')

    def is_action_valid(self, g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        assert skill.is_card(equipment.GungnirSkill)
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return definition.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(self, act):
        # for LaunchCard.effect_string
        source = act.source
        target = act.target
        s = '|G【%s】|r发动了|G冈格尼尔|r之枪，将两张牌当作|G弹幕|r对|G【%s】|r使用。' % (
            source.ui_meta.name,
            target.ui_meta.name,
        )
        return s

    def sound_effect(self, act):
        return definition.AttackCard.ui_meta.sound_effect(act)


@ui_meta(definition.ScarletRhapsodyCard)
class ScarletRhapsodyCard:
    # action_stage meta
    name = '绯想之剑'
    image = 'thb-card-scarletrhapsodysword'
    image_small = 'thb-card-small-scarletrhapsodysword'
    description = (
        '|R绯想之剑|r\n'
        '\n'
        '攻击范围4，装备后：当你使用的|G弹幕|r是你的最后一张手牌时，你可以为此|G弹幕|r指定至多三名目标。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.ScarletRhapsodySkill)
class ScarletRhapsodySkill:
    # Skill
    name = '绯想之剑'

    def clickable(self, game):
        me = game.me
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return act.target is me

        except IndexError:
            pass

        return False

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(equipment.ScarletRhapsodySkill)
        if not skill.check():
            return (False, '请选择你的最后一张【弹幕】！')
        else:
            if not target_list:
                return (False, '请选择弹幕的目标（最多可以选择3名玩家）')

            if g.me in target_list:
                return (True, '您真的要自残么？！')
            else:
                return (True, '全人类的绯想天！')

    def effect_string(self, act: actions.LaunchCard) -> Optional[str]:
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        tl = BatchList(act.target_list)

        return '全人类的绯想天，当然不能只打一个！于是|G【%s】|r选了|G【%s】|r一共%d个目标！' % (
            src.ui_meta.name,
            '】|r、|G【'.join(tl.ui_meta.name),
            len(tl),
        )

    def sound_effect(self, act):
        return 'thb-cv-card_srs'


@ui_meta(definition.RepentanceStickCard)
class RepentanceStickCard:
    # action_stage meta
    name = '悔悟棒'
    image = 'thb-card-repentancestick'
    image_small = 'thb-card-small-repentancestick'
    description = (
        '|R悔悟棒|r\n'
        '\n'
        '攻击范围2，装备后：当你使用|G弹幕|r造成伤害时，你可以防止此伤害，改为依次弃置目标角色区域内的两张牌。\n'
        '|B|R>> |r 区域内的牌包括手牌，装备区的牌和判定区的牌\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.RepentanceStickSkill)
class RepentanceStickSkill:
    # Skill
    name = '悔悟棒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.RepentanceStickHandler)
class RepentanceStickHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【悔悟棒】吗？'


@ui_meta(equipment.RepentanceStick)
class RepentanceStick:
    def effect_string_before(self, act):
        return (
            '|G【%s】|r用|G悔悟棒|r狠狠的敲了|G【%s】|r一通…'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,

        )

    def effect_string(self, act: equipment.RepentanceStick) -> str:
        cl = BatchList[Card](act.cards)
        return '又抢过|G【%s】|r的|G%s|r扔了出去！' % (
            act.target.ui_meta.name,
            '|r和|G'.join(cl.ui_meta.name)
        )

    def sound_effect(self, act):
        return 'thb-cv-card_repentancestick'


@ui_meta(definition.IbukiGourdCard)
class IbukiGourdCard:
    # action_stage meta
    name = '伊吹瓢'
    image = 'thb-card-ibukigourd'
    image_small = 'thb-card-small-ibukigourd'
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string

    description = (
        '|R伊吹瓢|r\n\n'
        '装备后：获得立即|B喝醉|r状态。并且，若你在出牌阶段没有造成过伤害，在回合结束阶段获得|B喝醉|r状态。\n\n'
        '|DB（画师：霏茶）|r'
    )


@ui_meta(equipment.IbukiGourdSkill)
class IbukiGourdSkill:
    # Skill
    name = '伊吹瓢'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(definition.HouraiJewelCard)
class HouraiJewelCard:
    # action_stage meta
    name = '蓬莱玉枝'
    image = 'thb-card-houraijewel'
    image_small = 'thb-card-small-houraijewel'
    description = (
        '|R蓬莱玉枝|r\n'
        '\n'
        '攻击范围1。装备后，你使用的|G弹幕|r时，可以将弹幕的效果转化成如下的符卡效果：造成1点伤害。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.HouraiJewelSkill)
class HouraiJewelSkill:
    # Skill
    name = '蓬莱玉枝'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.HouraiJewelHandler)
class HouraiJewelHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【蓬莱玉枝】吗？'


@ui_meta(equipment.HouraiJewelAttack)
class HouraiJewelAttack:
    def effect_string_apply(self, act):
        return (
            '|G【%s】|r发动了|G蓬莱玉枝|r，包裹着魔法核心的弹幕冲向了|G【%s】|r！'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(definition.MaidenCostumeCard)
class MaidenCostumeCard:
    # action_stage meta
    name = '巫女服'
    image = 'thb-card-maidencostume'
    image_small = 'thb-card-small-maidencostume'
    description = (
        '|R巫女服|r\n\n'
        '装备后：当你成为一张符卡的目标时，你可以进行一次判定：若判定牌点数为9到K，则视为你使用了一张|G好人卡|r。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.MaidenCostume)
class MaidenCostume:
    # Skill
    name = '巫女服'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    def sound_effect(self, act):
        return 'thb-cv-card_maidencostume'


@ui_meta(equipment.MaidenCostumeHandler)
class MaidenCostumeHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【巫女服】吗？'


@ui_meta(equipment.MaidenCostumeAction)
class MaidenCostumeAction:
    fatetell_display_name = '巫女服'

    def effect_string_before(self, act):
        return (
            '|G【%s】|r穿了|G巫女服|r，春度爆表，不怕符卡！'
        ) % (
            act.source.ui_meta.name,
        )

    def effect_string(self, act):
        if not act.succeeded:
            return (
                '好像|G【%s】|r的春度还是不够用…'
            ) % (
                act.source.ui_meta.name,
            )


@ui_meta(definition.HakuroukenCard)
class HakuroukenCard:
    # action_stage meta
    name = '白楼剑'
    image = 'thb-card-hakurouken'
    image_small = 'thb-card-small-hakurouken'
    description = (
        '|R白楼剑|r\n\n'
        '攻击范围2，装备后：当你使用的草花色|G弹幕|r指定一名目标角色后，你可以令其选择一项：\n'
        '|B|R>> |r弃置一张手牌\n'
        '|B|R>> |r令你摸一张牌\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.HakuroukenSkill)
class HakuroukenSkill:
    # Skill
    name = '白楼剑'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.Hakurouken)
class Hakurouken:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '弃置这张牌')
        else:
            return (False, '请弃掉一张牌（否则对方摸一张牌）')

    def effect_string_before(self, act):
        return (
            '|G【%s】|r祭起了|G白楼剑|r，试图斩断|G【%s】|r的迷惘！'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def effect_string(self, act):
        if act.peer_action == 'drop':
            return '|G【%s】|r弃置了一张牌。' % act.target.ui_meta.name
        else:
            return None  # DrawCards has it's own prompt

    def sound_effect(self, act):
        return 'thb-cv-card_hakurouken'


@ui_meta(equipment.HakuroukenHandler)
class HakuroukenHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【白楼剑】吗？'


@ui_meta(definition.AyaRoundfanCard)
class AyaRoundfanCard:
    # action_stage meta
    name = '团扇'
    image = 'thb-card-ayaroundfan'
    image_small = 'thb-card-small-ayaroundfan'
    description = (
        '|R团扇|r\n'
        '\n'
        '攻击距离5，装备后：当你使用的|G弹幕|r对目标角色造成伤害时，你可以弃置一张手牌，然后弃置其装备区里的一张牌。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.AyaRoundfanSkill)
class AyaRoundfanSkill:
    # Skill
    name = '团扇'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.AyaRoundfanHandler)
class AyaRoundfanHandler:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '这种妨碍拍摄的东西，统统脱掉！')
        else:
            return (False, '请弃掉一张手牌发动团扇（否则不发动）')


@ui_meta(equipment.AyaRoundfan)
class AyaRoundfan:
    def effect_string_before(self, act):
        return (
            '|G【%s】|r觉得手中的|G团扇|r用起来好顺手，便加大力度试了试…'
        ) % (
            act.source.ui_meta.name,
        )

    def effect_string(self, act):
        return (
            '于是|G【%s】|r的|G%s|r就飞了出去！'
        ) % (
            act.target.ui_meta.name,
            act.card.ui_meta.name,
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-card_roundfan1',
            'thb-cv-card_roundfan2',
        ])


@ui_meta(definition.NenshaPhoneCard)
class NenshaPhoneCard:
    # action_stage meta
    name = '念写机'
    image = 'thb-card-nenshaphone'
    image_small = 'thb-card-small-nenshaphone'
    description = (
        '|R念写机|r\n'
        '\n'
        '攻击距离4，装备后：当你使用的|G弹幕|r对目标角色造成伤害后，可以将其两张手牌置入明牌区。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶）|r'

    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.NenshaPhoneSkill)
class NenshaPhoneSkill:
    # Skill
    name = '念写机'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.NenshaPhoneHandler)
class NenshaPhoneHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【念写机】吗？'


@ui_meta(equipment.NenshaPhone)
class NenshaPhone:
    def effect_string(self, act):
        return (
            '|G【%s】|r表示，将|G【%s】|r推倒后拍摄胖次，是记者的自我修养中不可或缺的一部分。'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-card_nenshaphone'


@ui_meta(definition.LaevateinCard)
class LaevateinCard:
    # action_stage meta
    name = '莱瓦汀'
    image = 'thb-card-laevatein'
    image_small = 'thb-card-small-laevatein'
    description = (
        '|R莱瓦汀|r\n'
        '\n'
        '攻击距离3，装备后：当你使用的|G弹幕|r被目标角色使用的|G擦弹|r抵消时，你可以弃置两张牌，令此|G弹幕|r依然生效。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.LaevateinSkill)
class LaevateinSkill:
    # Skill
    name = '莱瓦汀'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.LaevateinHandler)
class LaevateinHandler:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '灭世之炎岂能轻易闪过！')
        else:
            return (False, '请弃掉两张牌发动莱瓦汀（否则不发动）')


@ui_meta(equipment.Laevatein)
class Laevatein:
    def effect_string_before(self, act):
        return '|G莱瓦汀|r的灭世之炎岂能轻易闪过！'

    def sound_effect(self, act):
        return 'thb-cv-card_laevatein'


@ui_meta(definition.DeathSickleCard)
class DeathSickleCard:
    # action_stage meta
    name = '死神之镰'
    image = 'thb-card-deathsickle'
    image_small = 'thb-card-small-deathsickle'
    description = (
        '|R死神之镰|r\n'
        '\n'
        '攻击范围2，装备后：当你使用的【弹幕】对目标角色造成伤害时，若其没有手牌，此伤害+1。\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.DeathSickleSkill)
class DeathSickleSkill:
    # Skill
    name = '死神之镰'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.DeathSickle)
class DeathSickle:
    def effect_string(self, act):
        return (
            '|G【%s】|r看到|G【%s】|r一副丧家犬的模样，'
            '手中的|G死神之镰|r不自觉地一狠…'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-card_deathsickle'


@ui_meta(definition.KeystoneCard)
class KeystoneCard:
    # action_stage meta
    name = '要石'
    image = 'thb-card-keystone'
    image_small = 'thb-card-small-keystone'
    description = (
        '|R要石|r\n\n'
        '特殊的绿色UFO装备，距离+1\n'
        '装备后跳过【罪袋】对你的结算。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.KeystoneSkill)
class KeystoneSkill:
    # Skill
    name = '要石'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.Keystone)
class Keystone:
    def effect_string(self, act):
        return '|G【%s】|r站在|G要石|r上，照着|G罪袋|r的脸一脚踹了下去！' % (
            act.target.ui_meta.name
        )

    def sound_effect(self, act):
        return 'thb-cv-card_keystone'


@ui_meta(definition.WitchBroomCard)
class WitchBroomCard:
    # action_stage meta
    name = '魔女扫把'
    image = 'thb-card-witchbroom'
    image_small = 'thb-card-small-witchbroom'
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string
    description = (
        '|R魔女扫把|r\n\n'
        '特殊的红色UFO装备，距离-2。\n\n'
        '|DB（画师：霏茶）|r'
    )


@ui_meta(equipment.WitchBroomSkill)
class WitchBroomSkill:
    # Skill
    no_display = True


@ui_meta(definition.YinYangOrbCard)
class YinYangOrbCard:
    # action_stage meta
    name = '阴阳玉'
    image = 'thb-card-yinyangorb'
    image_small = 'thb-card-small-yinyangorb'
    description = (
        '|R阴阳玉|r\n\n'
        '装备后：在你的判定牌生效前，你可以用装备区内的|G阴阳玉|r替换之。\n\n'
        '|DB（画师：霏茶）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.YinYangOrbSkill)
class YinYangOrbSkill:
    # Skill
    name = '阴阳玉'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.YinYangOrbHandler)
class YinYangOrbHandler:
    # choose_option
    choose_option_buttons = (('替换', True), ('不替换', False))
    choose_option_prompt = '你要使用【阴阳玉】替换当前的判定牌吗？'


@ui_meta(equipment.YinYangOrb)
class YinYangOrb:
    def effect_string(self, act):
        return '|G【%s】|r用|G%s|r替换了她的判定牌' % (
            act.target.ui_meta.name,
            card_desc(act.card),
        )


@ui_meta(definition.SuwakoHatCard)
class SuwakoHatCard:
    # action_stage meta
    name = '青蛙帽'
    image = 'thb-card-suwakohat'
    image_small = 'thb-card-small-suwakohat'
    description = (
        '|R青蛙帽|r\n\n'
        '装备后：手牌上限+2\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.SuwakoHatSkill)
class SuwakoHatSkill:
    # Skill
    name = '青蛙帽'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.SuwakoHatEffect)
class SuwakoHatEffect:
    def sound_effect(self, act):
        return 'thb-cv-card_suwakohat'


@ui_meta(definition.YoumuPhantomCard)
class YoumuPhantomCard:
    # action_stage meta
    name = '半灵'
    image = 'thb-card-phantom'
    image_small = 'thb-card-small-phantom'
    description = (
        '|R半灵|r\n\n'
        '装备后：增加1点体力上限，当失去装备区里的【半灵】时，你回复1点体力。\n\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.YoumuPhantomSkill)
class YoumuPhantomSkill:
    # Skill
    name = '半灵'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.YoumuPhantomHeal)
class YoumuPhantomHeal:
    def sound_effect(self, act):
        return 'thb-cv-card_phantom'


@ui_meta(definition.IceWingCard)
class IceWingCard:
    # action_stage meta
    name = '⑨的翅膀'
    image = 'thb-card-icewing'
    image_small = 'thb-card-small-icewing'
    description = (
        '|R⑨的翅膀|r\n\n'
        '特殊的红色UFO装备，距离-1。\n\n'
        '装备后：|G封魔阵|r和|G冻青蛙|r对你无效。\n\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.IceWingSkill)
class IceWingSkill:
    # Skill
    name = '⑨的翅膀'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(equipment.IceWing)
class IceWing:
    def effect_string(self, act):
        return '|G【%s】|r借着|G⑨的翅膀|r飞了出来，|G%s|r没起到什么作用' % (
            act.target.ui_meta.name,
            act.action.associated_card.ui_meta.name,
        )

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
    image = 'thb-card-grimoire'
    image_small = 'thb-card-small-grimoire'
    description = (
        '|R魔导书|r\n'
        '\n'
        '攻击距离1，装备后，你可以消耗一点干劲并将一张牌按照以下规则使用：\n'
        '|B|R>> |r黑桃♠视为|G百鬼夜行|r\n'
        '|B|R>> |r红桃♥视为|G宴会|r\n'
        '|B|R>> |r梅花♣视为|G地图炮|r\n'
        '|B|R>> |r方片♦视为|G五谷丰登|r\n'
        '\n'
        '|R出牌阶段你可以消耗1点干劲重铸手牌中的武器|r\n'
        '\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )
    is_action_valid = equip_iav
    effect_string = suppress_launch_card_effect_string


@ui_meta(equipment.GrimoireSkill)
class GrimoireSkill:
    # Skill
    name = '魔导书'

    def clickable(self, game):
        me = game.me
        t = me.tags
        if t['grimoire_tag'] >= t['turn_count']:
            return False

        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                if me.tags['freeattack'] >= me.tags['turn_count']:
                    return True

                if me.tags['vitality'] > 0:
                    return True

                if me.has_skill(equipment.ElementalReactorSkill):
                    return True

        except IndexError:
            pass

        return False

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(equipment.GrimoireSkill)
        acards = skill.associated_cards
        if not (len(acards)) == 1:
            return (False, '请选择一张牌')
        else:
            s = skill.lookup_tbl[acards[0].suit].ui_meta.name
            return (True, '发动【%s】' % s)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        return (
            '|G【%s】|r抓起一张牌放入|G魔导书|r' +
            '，念动咒语，发动了|G%s|r。'
        ) % (
            source.ui_meta.name,
            card.lookup_tbl[card.associated_cards[0].suit].ui_meta.name
        )

    def sound_effect(self, act):
        return 'thb-cv-card_grimoire'


@ui_meta(equipment.SinsackHatAction)
class SinsackHatAction:
    fatetell_display_name = '头套'

    def effect_string_before(self, act):
        return '看着戴着|G头套|r的|G【%s】|r，真正的的罪袋们都兴奋了起来！' % (
            act.target.ui_meta.name,
        )


@ui_meta(equipment.SinsackHat)
class SinsackHat:
    # Skill
    name = '头套'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(definition.SinsackHatCard)
class SinsackHatCard:
    # action_stage meta
    name = '头套'
    image = 'thb-card-sinsackhat'
    image_small = 'thb-card-small-sinsackhat'
    description = (
        '|R罪袋的头套|r\n\n'
        '对距离2以内的一名角色使用\n'
        '装备|G罪袋的头套|r的角色需在判定阶段后进行一次判定，若为黑桃1-8，则目标角色受到2点伤害，并且将|G罪袋的头套|r收入手牌。\n'
        '|DB（画师：霏茶，CV：大白）|r'
    )

    def is_action_valid(self, g, cl, target_list):
        if not target_list:
            return (False, '请选择目标')
        t = target_list[0]
        if g.me is t:
            return (True, '真的要自己戴上吗？')
        return (True, '是这样的，这个不是胖次……不不，真的没有胖次')

    effect_string = suppress_launch_card_effect_string
