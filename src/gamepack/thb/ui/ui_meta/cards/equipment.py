# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards

from gamepack.thb.ui.ui_meta.common import gen_metafunc, card_desc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid

from gamepack.thb.ui.resource import resource as gres


from utils import BatchList
__metaclass__ = gen_metafunc(cards)


def equip_iav(g, cl, target_list):
    return (True, u'配上好装备，不再掉节操！')


class OpticalCloakCard:
    # action_stage meta
    name = u'光学迷彩'
    image = gres.card_opticalcloak
    image_small = gres.card_opticalcloak_small
    description = (
        u'|R光学迷彩|r\n\n'
        u'装备【光学迷彩】后，每次需要出【擦弹】时（例如受到【弹幕】或【地图炮】攻击时），可以选择判定，若判定结果为红色花色（红桃或方块），则等效于出了一张【擦弹】；否则需再出【擦弹】。'
    )

    is_action_valid = equip_iav


class OpticalCloakSkill:
    # Skill
    name = u'光学迷彩'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class OpticalCloakHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【光学迷彩】吗？'


class OpticalCloak:
    fatetell_display_name = u'光学迷彩'

    def effect_string_before(act):
        return u'|G【%s】|r祭起了|G光学迷彩|r…' % (
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        if act.succeeded:
            return u'效果拔群！'
        else:
            return u'但是被看穿了…'


class MomijiShieldCard:
    # action_stage meta
    name = u'天狗盾'
    image = gres.card_momijishield
    image_small = gres.card_momijishield_small
    description = (
        u'|R天狗盾|r\n\n'
        u'装备后，黑色【弹幕】对你无效。'
    )

    is_action_valid = equip_iav


class MomijiShieldSkill:
    # Skill
    name = u'天狗盾'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MomijiShield:
    def effect_string(act):
        return u'被|G天狗盾|r挡下了…'


ufo_desc = (
    u'|R%s|r\n\n'
    u'UFO用来改变自己与其他玩家之间的距离。\n'
    u'|B|R>> |r红色UFO为进攻用，当你计算和其它玩家的距离时,在原有的基础上减少相应距离，若结果小于1则依然视为1。\n'
    u'|B|R>> |r绿色UFO为防守用，当其它玩家计算和你的距离时,在原有的基础上增加相应距离。\n'
    u'|B|R>> |r你可以同时装备两种UFO'
)


class GreenUFOCard:
    # action_stage meta
    name = u'绿色UFO'
    image = gres.card_greenufo
    image_small = gres.card_greenufo_small
    description = ufo_desc % name

    is_action_valid = equip_iav


class GreenUFOSkill:
    # Skill
    name = u'绿色UFO'
    no_display = True
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class RedUFOCard:
    # action_stage meta
    name = u'红色UFO'
    image = gres.card_redufo
    image_small = gres.card_redufo_small
    description = ufo_desc % name

    is_action_valid = equip_iav


class RedUFOSkill:
    # Skill
    name = u'红色UFO'
    no_display = True
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class RoukankenCard:
    # action_stage meta
    name = u'楼观剑'
    image = gres.card_roukanken
    image_small = gres.card_roukanken_small
    description = (
        u'|R楼观剑|r\n\n'
        u'攻击范围3，每当你使用【弹幕】攻击一名角色时，无视该角色的防具。'
    )
    is_action_valid = equip_iav


class RoukankenSkill:
    # Skill
    name = u'楼观剑'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Roukanken:
    def effect_string_apply(act):
        return u'没有什么防具是|G楼观剑|r斩不断的！'


class ElementalReactorCard:
    # action_stage meta
    name = u'八卦炉'
    image = gres.card_reactor
    image_small = gres.card_reactor_small
    description = (
        u'|R八卦炉|r\n\n'
        u'攻击范围1，出牌阶段可以使用任意张【弹幕】。'
    )

    is_action_valid = equip_iav


class ElementalReactorSkill:
    # Skill
    name = u'八卦炉'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UmbrellaCard:
    # action_stage meta
    name = u'阳伞'
    image = gres.card_umbrella
    image_small = gres.card_umbrella_small
    description = (
        u'|R阳伞|r\n\n'
        u'装备后符卡造成的伤害对你无效。'
    )

    is_action_valid = equip_iav


class UmbrellaSkill:
    # Skill
    name = u'紫的阳伞'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UmbrellaEffect:
    def effect_string_before(act):
        a = act.action
        card = getattr(a, 'associated_card', None)
        s = u'|G%s|r' % card.ui_meta.name if card else u''
        return u'|G【%s】|r受到的%s效果被|G阳伞|r挡下了' % (
            act.target.ui_meta.char_name,
            s,
        )


class GungnirCard:
    # action_stage meta
    name = u'冈格尼尔'
    image = gres.card_gungnir
    image_small = gres.card_gungnir_small
    description = (
        u'|R冈格尼尔|r\n\n'
        u'攻击范围3，当你需要使用或打出一张【弹幕】时，你可以将两张手牌当一张【弹幕】来使用或打出。'
    )

    is_action_valid = equip_iav


class GungnirSkill:
    # Skill
    name = u'冈格尼尔'

    def clickable(g):
        try:
            act = g.hybrid_stack[-1]
            if act.cond([cards.GungnirSkill(g.me)]):
                return True

        except (IndexError, AttributeError):
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        assert skill.is_card(cards.GungnirSkill)
        acards = skill.associated_cards
        if len(acards) != 2:
            return (False, u'请选择2张手牌！')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in acards):
            return (False, u'只能使用手牌发动！')
        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        assert skill.is_card(cards.GungnirSkill)
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.effect_string
        source = act.source
        target = act.target
        s = u'|G【%s】|r发动了|G冈格尼尔|r之枪，将两张牌当作|G弹幕|r对|G【%s】|r使用。' % (
            source.ui_meta.char_name,
            target.ui_meta.char_name,
        )
        return s


class ScarletRhapsodyCard:
    # action_stage meta
    name = u'绯想之剑'
    image = gres.card_scarletrhapsodysword
    image_small = gres.card_scarletrhapsodysword_small
    description = (
        u'|R绯想之剑|r\n\n'
        u'攻击范围4，当你使用的【弹幕】是你的最后一张手牌时，你可以为这张【弹幕】指定至多三名目标，然后依次结算之。'
    )

    is_action_valid = equip_iav


class ScarletRhapsodySkill:
    # Skill
    name = u'绯想之剑'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                cl = list(me.cards) + list(me.showncards)
                if len(cl) == 1:
                    return True

        except IndexError:
            pass

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(cards.ScarletRhapsodySkill)
        acards = skill.associated_cards
        if not (len(acards) == 1 and acards[0].is_card(cards.AttackCard)):
            return (False, u'请选择你的最后一张【弹幕】！')
        else:
            if not target_list:
                return (False, u'请选择弹幕的目标（最多可以选择3名玩家）')

            if g.me in target_list:
                return (True, u'您真的要自残么？！')
            else:
                return (True, u'全人类的绯想天！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        tl = BatchList(act.target_list)

        return u'全人类的绯想天，当然不能只打一个！于是|G【%s】|r选了|G【%s】|r一共%d个目标！' % (
            source.ui_meta.char_name,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
            len(tl),
        )


class RepentanceStickCard:
    # action_stage meta
    name = u'悔悟棒'
    image = gres.card_repentancestick
    image_small = gres.card_repentancestick_small
    description = (
        u'|R悔悟棒|r\n\n'
        u'攻击范围2，当你使用【弹幕】造成伤害时，你可以防止此伤害，改为弃置该目标角色的两张牌（弃完第一张再弃第二张）。'
    )

    is_action_valid = equip_iav


class RepentanceStickSkill:
    # Skill
    name = u'悔悟棒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class RepentanceStickHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【悔悟棒】吗？'


class RepentanceStick:
    def effect_string_before(act):
        return (
            u'|G【%s】|r用|G悔悟棒|r狠狠的敲了|G【%s】|r一通…'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,

        )

    def effect_string(act):
        cl = BatchList(act.cards)
        return u'又抢过|G【%s】|r的|G%s|r扔了出去！' % (
            act.target.ui_meta.char_name,
            u'|r和|G'.join(cl.ui_meta.name)
        )


class MaidenCostumeEffect:
    def effect_string(act):
        return u'|G【%s】|r美美的穿着巫女服，却在危险来到的时候踩到了裙边……' % (
            act.target.ui_meta.char_name,
        )


class MaidenCostumeCard:
    # action_stage meta
    name = u'巫女服'
    image = gres.card_maidencostume
    image_small = gres.card_maidencostume_small
    description = (
        u'|R巫女服|r\n\n'
        u'距离限制2，你可以将这张牌置于任意一名处于距离内的玩家的装备区里。\n'
        u'受到【罪袋狂欢】效果时，无法回避。'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择目标')
        t = target_list[0]
        if g.me is t:
            return (True, u'真的要自己穿上吗？')
        return (True, u'\腋/！')


class MaidenCostumeSkill:
    # Skill
    name = u'巫女服'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class IbukiGourdCard:
    # action_stage meta
    name = u'伊吹瓢'
    image = gres.card_ibukigourd
    image_small = gres.card_ibukigourd_small
    is_action_valid = equip_iav
    description = (
        u'|R伊吹瓢|r\n\n'
        u'当装备在进攻马位置。在装备、失去装备及回合结束时获得|B喝醉|r状态'
    )


class IbukiGourdSkill:
    # Skill
    name = u'伊吹瓢'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class HouraiJewelCard:
    # action_stage meta
    name = u'蓬莱玉枝'
    image = gres.card_houraijewel
    image_small = gres.card_houraijewel_small
    description = (
        u'|R蓬莱玉枝|r\n\n'
        u'攻击范围1，当使用【弹幕】时可以选择发动。发动后【弹幕】带有符卡性质，可以被【好人卡】抵消，不可以使用【擦弹】躲过。\n'
        u'|B|R>> |r计算在出【弹幕】的次数内。\n'
        u'|B|R>> |r蓬莱玉枝造成的伤害为固定的1点'
    )

    is_action_valid = equip_iav


class HouraiJewelSkill:
    # Skill
    name = u'蓬莱玉枝'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class HouraiJewelHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【蓬莱玉枝】吗？'


class HouraiJewelAttack:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r发动了|G蓬莱玉枝|r，包裹着魔法核心的弹幕冲向了|G【%s】|r！'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class SaigyouBranchCard:
    # action_stage meta
    name = u'西行妖'
    image = gres.card_saigyoubranch
    image_small = gres.card_saigyoubranch_small
    description = (
        u'|R西行妖|r\n\n'
        u'每当你成为其他人符卡的目标时，你可以进行一次判定：若判定牌点数为9到K，则视为你使用了一张【好人卡】。'
    )
    is_action_valid = equip_iav


class SaigyouBranchSkill:
    # Skill
    name = u'西行妖'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SaigyouBranchHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【西行妖】吗？'


class SaigyouBranch:
    fatetell_display_name = u'西行妖'

    def effect_string_before(act):
        return (
            u'|G西行妖|r的枝条受到了|G【%s】|r春度的滋养，'
            u'在关键时刻突然撑出一片结界，试图将符卡挡下！'
        ) % (
            act.source.ui_meta.char_name,
        )

    def effect_string(act):
        if not act.succeeded:
            return (
                u'但是很明显|G【%s】|r的春度不够用了…'
            ) % (
                act.source.ui_meta.char_name,
            )


class HakuroukenCard:
    # action_stage meta
    name = u'白楼剑'
    image = gres.card_hakurouken
    image_small = gres.card_hakurouken_small
    description = (
        u'|R白楼剑|r\n\n'
        u'攻击范围2，当你使用【弹幕】指定了一名角色为目标后，若此弹幕为黑色，你可以令对方选择一项：\n'
        u'|B|R>> |r弃一张手牌\n'
        u'|B|R>> |r你摸一张牌'
    )
    is_action_valid = equip_iav


class HakuroukenSkill:
    # Skill
    name = u'白楼剑'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Hakurouken:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置这张牌')
        else:
            return (False, u'请弃掉一张牌（否则对方摸一张牌）')

    def effect_string_before(act):
        return (
            u'|G【%s】|r祭起了|G白楼剑|r，试图斩断|G【%s】|r的迷惘！'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        if act.peer_action == 'drop':
            return u'|G【%s】|r弃置了一张牌。' % act.target.ui_meta.char_name
        else:
            return u'|G【%s】|r摸了一张牌。' % act.source.ui_meta.char_name


class HakuroukenHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【白楼剑】吗？'


class AyaRoundfanCard:
    # action_stage meta
    name = u'团扇'
    image = gres.card_ayaroundfan
    image_small = gres.card_ayaroundfan_small
    description = (
        u'|R团扇|r\n\n'
        u'攻击距离5，当你使用【弹幕】命中时，可以弃一张手牌，卸掉目标的一件装备。'
    )
    is_action_valid = equip_iav


class AyaRoundfanSkill:
    # Skill
    name = u'团扇'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AyaRoundfanHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'这种妨碍拍摄的东西，统统脱掉！')
        else:
            return (False, u'请弃掉一张手牌发动团扇（否则不发动）')


class AyaRoundfan:
    def effect_string_before(act):
        return (
            u'|G【%s】|r觉得手中的|G团扇|r用起来好顺手，便加大力度试了试…'
        ) % (
            act.source.ui_meta.char_name,
        )

    def effect_string(act):
        return (
            u'于是|G【%s】|r的|G%s|r就飞了出去！'
        ) % (
            act.target.ui_meta.char_name,
            act.card.ui_meta.name,
        )


class NenshaPhoneCard:
    # action_stage meta
    name = u'念写机'
    image = gres.card_nenshaphone
    image_small = gres.card_nenshaphone_small
    description = (
        u'|R念写机|r\n\n'
        u'攻击距离4，当你使用【弹幕】命中时，可以将目标的两张手牌置入明牌区。'
    )
    is_action_valid = equip_iav


class NenshaPhoneSkill:
    # Skill
    name = u'念写机'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class NenshaPhoneHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【念写机】吗？'


class NenshaPhone:
    def effect_string(act):
        return (
            u'|G【%s】|r表示，将|G【%s】|r推倒后拍摄胖次，是记者的自我修养中不可或缺的一部分。'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class LaevateinCard:
    # action_stage meta
    name = u'莱瓦汀'
    image = gres.card_laevatein
    image_small = gres.card_laevatein_small
    description = (
        u'|R莱瓦汀|r\n\n'
        u'攻击距离3，目标角色使用【擦弹】抵消你使用【弹幕】的效果时，你可以弃两张牌（可以是手牌也可以是自己的其它装备牌），使此【弹幕】强制命中对方，无法闪避。'
    )
    is_action_valid = equip_iav


class LaevateinSkill:
    # Skill
    name = u'莱瓦汀'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LaevateinHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'灭世之炎岂能轻易闪过！')
        else:
            return (False, u'请弃掉两张牌发动莱瓦汀（否则不发动）')


class Laevatein:
    def effect_string_before(act):
        return u'|G莱瓦汀|r的灭世之炎岂能轻易闪过！'


class DeathSickleCard:
    # action_stage meta
    name = u'死神之镰'
    image = gres.card_deathsickle
    image_small = gres.card_deathsickle_small
    description = (
        u'|R死神之镰|r\n\n'
        u'攻击范围2，|B锁定技|r，当你使用的【弹幕】造成伤害时，若目标没有手牌，此【弹幕】的伤害+1。'
    )
    is_action_valid = equip_iav


class DeathSickleSkill:
    # Skill
    name = u'死神之镰'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DeathSickle:
    def effect_string(act):
        return (
            u'|G【%s】|r看到|G【%s】|r一副丧家犬的模样，'
            u'手中的|G死神之镰|r不自觉地一狠…'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class KeystoneCard:
    # action_stage meta
    name = u'要石'
    image = gres.card_keystone
    image_small = gres.card_keystone_small
    description = (
        u'|R要石|r\n\n'
        u'特殊的绿色UFO装备，距离+1\n'
        u'装备后不受【罪袋】的影响'
    )
    is_action_valid = equip_iav


class KeystoneSkill:
    # Skill
    name = u'要石'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Keystone:
    def effect_string(act):
        return u'|G【%s】|r站在|G要石|r上，照着|G罪袋|r的脸一脚踹了下去！' % (
            act.target.ui_meta.char_name
        )


class WitchBroomCard:
    # action_stage meta
    name = u'魔女扫把'
    image = gres.card_witchbroom
    image_small = gres.card_witchbroom_small
    is_action_valid = equip_iav
    description = (
        u'|R魔女扫把|r\n\n'
        u'特殊的红色UFO装备，距离-2'
    )


class WitchBroomSkill:
    # Skill
    no_display = True


class YinYangOrbCard:
    # action_stage meta
    name = u'阴阳玉'
    image = gres.card_yinyangorb
    image_small = gres.card_yinyangorb_small
    description = (
        u'|R阴阳玉|r\n\n'
        u'当你的判定牌即将生效时，可以用装备着的【阴阳玉】代替判定牌生效。'
    )
    is_action_valid = equip_iav


class YinYangOrbSkill:
    # Skill
    name = u'阴阳玉'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class YinYangOrbHandler:
    # choose_option
    choose_option_buttons = ((u'替换', True), (u'不替换', False))
    choose_option_prompt = u'你要使用【阴阳玉】替换当前的判定牌吗？'


class YinYangOrb:
    def effect_string(act):
        return (
            u'|G【%s】|r用|G%s|r代替了她的判定牌'
        ) % (
            act.target.ui_meta.char_name,
            card_desc(act.card),
        )


class SuwakoHatCard:
    # action_stage meta
    name = u'青蛙帽'
    image = gres.card_suwakohat
    image_small = gres.card_suwakohat_small
    description = (
        u'|R青蛙帽|r\n\n'
        u'装备后，手牌上限+2'
    )
    is_action_valid = equip_iav


class SuwakoHatSkill:
    # Skill
    name = u'青蛙帽'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class YoumuPhantomCard:
    # action_stage meta
    name = u'半灵'
    image = gres.card_phantom
    image_small = gres.card_phantom_small
    description = (
        u'|R半灵|r\n\n'
        u'装备时增加一点体力上限，当失去装备区里的【半灵】时，回复一点体力。'
    )

    is_action_valid = equip_iav


class YoumuPhantomSkill:
    # Skill
    name = u'半灵'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class IceWingCard:
    # action_stage meta
    name = u'⑨的翅膀'
    image = gres.card_icewing
    image_small = gres.card_icewing_small
    description = (
        u'|R⑨的翅膀|r\n\n'
        u'装备后不受【封魔阵】和【冻青蛙】的影响。'
    )

    is_action_valid = equip_iav


class IceWingSkill:
    # Skill
    name = u'⑨的翅膀'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class IceWing:
    def effect_string(act):
        return u'|G【%s】|r借着|G⑨的翅膀|r飞了出来，|G%s|r没起到什么作用' % (
            act.target.ui_meta.char_name,
            act.action.associated_card.ui_meta.name,
        )


class GrimoireCard:
    # action_stage meta
    name = u'魔导书'
    image = gres.card_grimoire
    image_small = gres.card_grimoire_small
    description = (
        u'|R魔导书|r\n\n'
        u'攻击距离1，当在你的出牌阶段仍然可以使用【弹幕】时，你可以弃一张牌，发动魔导书，并且计入【弹幕】的使用次数，一回合限一次。\n'
        u'|B|R>> |r弃牌为红桃：视为发动【宴会】\n'
        u'|B|R>> |r弃牌为方片：视为发动【五谷丰登】\n'
        u'|B|R>> |r弃牌为黑桃：视为发动【罪袋狂欢】\n'
        u'|B|R>> |r弃牌为梅花：视为发动【地图炮】'
    )
    is_action_valid = equip_iav


class GrimoireSkill:
    # Skill
    name = u'魔导书'

    def clickable(game):
        me = game.me
        t = me.tags
        if t['grimoire_tag'] >= t['turn_count']:
            return False

        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                if me.tags['freeattack'] >= me.tags['turn_count']:
                    return True

                if me.tags['attack_num'] > 0:
                    return True

                if me.has_skill(cards.ElementalReactorSkill):
                    return True

        except IndexError:
            pass

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(cards.GrimoireSkill)
        acards = skill.associated_cards
        if not (len(acards)) == 1:
            return (False, u'请选择一张牌')
        else:
            s = skill.lookup_tbl[acards[0].suit].ui_meta.name
            return (True, u'发动【%s】' % s)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        return (
            u'|G【%s】|r抓起一张牌放入|G魔导书|r' +
            u'，念动咒语，发动了|G%s|r。'
        ) % (
            source.ui_meta.char_name,
            card.lookup_tbl[card.associated_cards[0].suit].ui_meta.name
        )
