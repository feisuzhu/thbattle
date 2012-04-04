# -*- coding: utf-8 -*-
from .. import actions
from .. import cards
from .. import characters

import game
import types
import resource as gres
from client.ui import resource as cres

from utils import DataHolder

def gen_metafunc(_for):
    def metafunc(clsname, bases, _dict):
        meta_for = _for.__dict__.get(clsname)
        data = DataHolder.parse(_dict)
        meta_for.ui_meta = data

    return metafunc

# -----BEGIN ACTIONS UI META-----
__metaclass__ = gen_metafunc(actions)

class DropCardStage:
    # choose_card meta
    text_valid = u'OK，就这些了'
    text = u'请弃牌…'


# -----END ACTIONS UI META-----

# -----BEGIN CARDS UI META-----
__metaclass__ = gen_metafunc(cards)

class HiddenCard:
    # action_stage meta
    image = cres.card_hidden
    name = u'这个是隐藏卡片，你不应该看到它'

    def is_action_valid(g, cl, target_list):
        return (False, u'这是BUG，你没法发动这张牌…')

class AttackCard:
    # action_stage meta
    image = gres.card_attack
    name = u'击'

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择击的目标')
        target = target_list[0]
        if target.dead:
            return (False, u'禁止鞭尸！')

        if g.me == target:
            return (True, u'您真的要自残么？！')
        else:
            return (True, u'来一发！')

class GrazeCard:
    # action_stage meta
    name = u'擦弹'
    image = gres.card_graze
    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动使用擦弹')

class WineCard:
    # action_stage meta
    name = u'酒'
    image = gres.card_wine
    def is_action_valid(g, cl, target_list):
        if g.me.tags.get('wine', False):
            return (True, u'你已经醉了，还要再喝吗？')
        return (True, u'三年陈酿，西瓜酒！')

class ExinwanCard:
    # action_stage meta
    name =u'恶心丸'
    image = gres.card_exinwan
    def is_action_valid(g, cl, target_list):
        return (True, u'哼，哼，哼哼……')

class ExinwanHandler:
    # choose_card meta
    text = u'请选择两张牌（不选则受到一点无源伤害）'
    text_valid = u'节操给你，离我远点！'

class UseGraze:
    # choose_card meta
    image = gres.card_graze
    text_valid = u'我闪！'
    text = u'请使用擦弹…'

class UseAttack:
    # choose_card meta
    text_valid = u'打架？来吧！'
    text = u'请打出一张击…'

class HealCard:
    # action_stage meta
    image = gres.card_heal
    name = u'麻薯'

    def is_action_valid(g, cl, target_list):
        target = target_list[0]
        if not g.me is target:
            return (False, u'BUG!!!!')

        if target.life >= target.maxlife:
            return (False, u'您已经吃饱了')
        else:
            return (True, u'来一口，精神焕发！')

class DemolitionCard:
    # action_stage meta
    image = gres.card_demolition
    name = u'城管执法'

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择拆除目标')

        target= target_list[0]
        if g.me is target:
            return (True, u'还是拆别人的吧…')
        elif not len(target.cards) + len(target.showncards) + len(target.equips) + len(target.fatetell):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'嗯，你的牌太多了')

class RejectCard:
    # action_stage meta
    name = u'好人卡'
    image = gres.card_reject

    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动出好人卡')

class RejectHandler:
    # choose_card meta
    text_valid = u'对不起，你是一个好人…'
    text = u'请选择一张好人卡'

class SealingArrayCard:
    # action_stage meta
    name = u'封魔阵'
    image = gres.card_sealarray
    tag_anim = gres.tag_sealarray

    def is_action_valid(g, cl, target_list):
        if len(target_list) != 1:
            return (False, u'请选择封魔阵的目标')
        t = target_list[0]
        if g.me is t:
            return (True, u'你不能跟自己过不去啊！')

        return (True, u'画个圈圈诅咒你！')

class NazrinRodCard:
    # action_stage meta
    name = u'探宝棒'
    image = gres.card_nazrinrod

    def is_action_valid(g, cl, target_list):
        t = target_list[0]
        assert t is g.me
        return (True, u'看看能找到什么好东西~')

class WorshiperCard:
    # action_stage meta
    name = u'罪袋'
    image = gres.card_zuidai
    tag_anim = gres.tag_zuidai

    def is_action_valid(g, cl, target_list):
        target = target_list[0]
        if not g.me == target:
            return (False, u'BUG!!!!')

        return (True, u'别来找我！')

def equip_iav(g, cl, target_list):
    t = target_list[0]
    assert t is g.me
    return (True, u'配上好装备，不再掉节操！')

class OpticalCloakCard:
    # action_stage meta
    name = u'光学迷彩'
    image = gres.card_opticalcloak
    image_small = gres.card_opticalcloak_small

    is_action_valid = equip_iav

class OpticalCloakSkill:
    # Skill
    name = u'光学迷彩'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class OpticalCloakHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【光学迷彩】吗？'

class GreenUFOCard:
    # action_stage meta
    name = u'绿色UFO'
    image = gres.card_greenufo
    image_small = gres.card_greenufo_small

    is_action_valid = equip_iav

class GreenUFOSkill:
    # Skill
    name = u'绿色UFO'
    no_display = True

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class RedUFOCard:
    # action_stage meta
    name = u'红色UFO'
    image = gres.card_redufo
    image_small = gres.card_redufo_small

    is_action_valid = equip_iav

class RedUFOSkill:
    # Skill
    name = u'红色UFO'
    no_display = True

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class YukariDimensionCard:
    # action_stage meta
    image = gres.card_yukaridimension
    name = u'紫的隙间'

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择目标')

        target= target_list[0]
        if g.me is target:
            return (True, u'你不能对自己使用隙间')
        elif not len(target.cards):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'请把胖次给我！')

class DuelCard:
    # action_stage meta
    image = gres.card_duel
    name = u'弹幕战'

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择弹幕战的目标')

        target= target_list[0]
        if g.me is target:
            return (True, u'你不能对自己使用弹幕战')
        else:
            return (True, u'来，战个痛快！')

class MapCannonCard:
    image = gres.card_mapcannon
    name = u'地图炮'

    def is_action_valid(g, cl, target_list):
        return (True, u'一个都不能跑！')

class WorshipersCarnivalCard:
    image = gres.card_worshiperscarnival
    name = u'罪袋狂欢'

    def is_action_valid(g, cl, target_list):
        return (True, u'罪袋们冲进来啦！')

class HakuroukenCard:
    # action_stage meta
    name = u'白楼剑'
    image = gres.card_hakurouken
    image_small = gres.card_hakurouken_small

    is_action_valid = equip_iav

class HakuroukenSkill:
    # Skill
    name = u'白楼剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class ElementalReactorCard:
    # action_stage meta
    name = u'八卦炉'
    image = gres.card_reactor
    image_small = gres.card_reactor_small

    is_action_valid = equip_iav

class ElementalReactorSkill:
    # Skill
    name = u'八卦炉'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class UmbrellaCard:
    # action_stage meta
    name = u'紫的阳伞'
    image = gres.card_umbrella
    image_small = gres.card_umbrella_small

    is_action_valid = equip_iav

class UmbrellaSkill:
    # Skill
    name = u'紫的阳伞'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class RoukankenCard:
    # action_stage meta
    name = u'楼观剑'
    image = gres.card_roukanken
    image_small = gres.card_roukanken_small

    is_action_valid = equip_iav

class RoukankenSkill:
    # Skill
    name = u'楼观剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class RoukankenHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【楼观剑】吗？'

class GungnirCard:
    # action_stage meta
    name = u'冈格尼尔'
    image = gres.card_gungnir
    image_small = gres.card_gungnir_small

    is_action_valid = equip_iav

class GungnirSkill:
    # Skill
    name = u'冈格尼尔'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[0]
            if isinstance(act, (actions.ActionStage, cards.UseAttack, cards.DollControl)):
                return True
        except IndexError:
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

    def is_action_valid(g, cl, source, target_list, is_complete=is_complete):
        skill = cl[0]
        assert skill.is_card(cards.GungnirSkill)
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|r发动了冈格尼尔之枪，将两张牌当作|c208020ff【击】|r对|c208020ff【%s】|r使用。' % (
            source.ui_meta.char_name,
            target.ui_meta.char_name,
        )
        return s

class LaevateinCard:
    # action_stage meta
    name = u'莱瓦汀'
    image = gres.card_laevatein
    image_small = gres.card_laevatein_small

    is_action_valid = equip_iav

class LaevateinSkill:
    # Skill
    name = u'莱瓦汀'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[0]
            if isinstance(act, actions.ActionStage):
                cl = list(me.cards) + list(me.showncards)
                if len(cl) == 1 and isinstance(cl[0], cards.AttackCard):
                    return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(cards.LaevateinSkill)
        acards = skill.associated_cards
        if not (len(acards) == 1 and acards[0].is_card(cards.AttackCard)):
            return (False, u'请选择你的最后一张【击】！')
        else:
            if not target_list:
                return (False, u'请选择击的目标（最多可以选择3名玩家）')

            if any(t.dead for t in target_list):
                return (False, u'禁止鞭尸！')

            if g.me in target_list:
                return (True, u'您真的要自残么？！')
            else:
                return (True, u'觉醒吧，禁忌的炎之魔剑！')

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|Laevatein!...|c208020ff【击】|r对|c208020ff【%s】|r使用。' % (
            source.ui_meta.char_name,
            target.ui_meta.char_name,
        )
        return s

class ThoridalCard:
    # action_stage meta
    name = u"Thori'dal"
    image = gres.card_thoridal
    image_small = gres.card_thoridal_small

    is_action_valid = equip_iav

class ThoridalSkill:
    # Skill
    name = u"Thori'dal"

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class RepentanceStickCard:
    # action_stage meta
    name = u'悔悟棒'
    image = gres.card_repentancestick
    image_small = gres.card_repentancestick_small

    is_action_valid = equip_iav

class RepentanceStickSkill:
    # Skill
    name = u'悔悟棒'
    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class RepentanceStickHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【悔悟棒】吗？'

class FeastCard:
    # action_stage meta
    image = gres.card_feast
    name = u'宴会'

    def is_action_valid(g, cl, target_list):
        return (True, u'开宴啦~~')

class HarvestCard:
    # action_stage meta
    image = gres.card_harvest
    name = u'五谷丰登'

    def is_action_valid(g, cl, target_list):
        return (True, u'麻薯会有的，节操是没有的！')

class MaidenCostumeCard:
    # action_stage meta
    name = u'巫女服'
    image = gres.card_maidencostume
    image_small = gres.card_maidencostume_small

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择目标')
        t = target_list[0]
        if g.me is t:
            return (True, u'真的要自己穿上吗？')
        return (True, u'腋！')

class MaidenCostumeSkill:
    # Skill
    name = u'巫女服'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class IbukiGourdCard:
    # action_stage meta
    name = u'伊吹瓢'
    image = gres.card_ibukigourd
    image_small = gres.card_ibukigourd_small
    is_action_valid = equip_iav

class IbukiGourdSkill:
    # Skill
    name = u'伊吹瓢'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class HouraiJewelCard:
    # action_stage meta
    name = u'蓬莱玉枝'
    image = gres.card_houraijewel
    image_small = gres.card_houraijewel_small
    is_action_valid = equip_iav

class HouraiJewelSkill:
    # Skill
    name = u'蓬莱玉枝'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class HouraiJewelHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【蓬莱玉枝】吗？'

class SaigyouBranchCard:
    # action_stage meta
    name = u'西行妖枝条'
    image = gres.card_saigyoubranch
    image_small = gres.card_saigyoubranch_small
    is_action_valid = equip_iav

class SaigyouBranchSkill:
    # Skill
    name = u'西行妖枝条'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class SaigyouBranch:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【西行妖枝条】吗？'

class FlirtingSwordCard:
    # action_stage meta
    name = u'调教剑'
    image = gres.card_flirtingsword
    image_small = gres.card_flirtingsword_small
    is_action_valid = equip_iav

class FlirtingSwordSkill:
    # Skill
    name = u'调教剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class FlirtingSword:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【调教剑】吗？'

    # choose_card
    text_valid = u'才……才不给你机会呢！'
    text = u'请弃掉一张牌（否则对方摸一张牌）'

class CameraCard:
    # action_stage meta
    name = u'文文的相机'
    image = gres.card_camera

    def is_action_valid(g, cl, tl):
        if not tl:
            return (False, u'请选择目标')
        t = tl[0]

        if not t.cards:
            return (True, u'这货已经没有隐藏的手牌了')

        return (True, u'摄影的境界，你们这些玩器材的永远都不会懂！')

class AyaRoundfanCard:
    # action_stage meta
    name = u'文文的团扇'
    image = gres.card_ayaroundfan
    image_small = gres.card_ayaroundfan_small
    is_action_valid = equip_iav

class AyaRoundfanSkill:
    # Skill
    name = u'文文的团扇'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class AyaRoundfan:
    # choose_card
    text_valid = u'这种妨碍拍摄的东西，统统脱掉！'
    text = u'请弃掉一张手牌发动团扇（否则不发动）'

class ScarletRhapsodySwordCard:
    # action_stage meta
    name = u'绯色之剑'
    image = gres.card_scarletrhapsodysword
    image_small = gres.card_scarletrhapsodysword_small
    is_action_valid = equip_iav

class ScarletRhapsodySwordSkill:
    # Skill
    name = u'绯色之剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class ScarletRhapsodySword:
    # choose_card
    text_valid = u'闪过头了！'
    text = u'请弃掉两张牌发动绯色之剑（否则不发动）'

class DeathSickleCard:
    # action_stage meta
    name = u'死神之镰'
    image = gres.card_deathsickle
    image_small = gres.card_deathsickle_small
    is_action_valid = equip_iav

class DeathSickleSkill:
    # Skill
    name = u'死神之镰'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class KeystoneCard:
    # action_stage meta
    name = u'要石'
    image = gres.card_keystone
    image_small = gres.card_keystone_small
    is_action_valid = equip_iav

class KeystoneSkill:
    # Skill
    name = u'要石'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')


class WitchBroomCard:
    # action_stage meta
    name = u'魔女的扫把'
    image = gres.card_witchbroom
    image_small = gres.card_witchbroom_small
    is_action_valid = equip_iav

class WitchBroomSkill:
    # Skill
    no_display = True
    '''
    name = u'绯色之剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')
    '''

class YinYangOrbCard:
    # action_stage meta
    name = u'阴阳玉'
    image = gres.card_yinyangorb
    image_small = gres.card_yinyangorb_small
    is_action_valid = equip_iav

class YinYangOrbSkill:
    # Skill
    name = u'阴阳玉'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class YinYangOrb:
    # choose_option
    choose_option_buttons = ((u'替换', True), (u'不替换', False))
    choose_option_prompt = u'你要使用【阴阳玉】替换当前的判定牌吗？'

class SuwakoHatCard:
    # action_stage meta
    name = u'青蛙帽'
    image = gres.card_suwakohat
    image_small = gres.card_suwakohat_small
    is_action_valid = equip_iav

class SuwakoHatSkill:
    # Skill
    name = u'青蛙帽'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')


class YoumuPhantomCard:
    # action_stage meta
    name = u'半灵'
    image = gres.card_youmuphantom
    image_small = gres.card_youmuphantom_small
    is_action_valid = equip_iav

class YoumuPhantomSkill:
    # Skill
    name = u'半灵'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class IceWingCard:
    # action_stage meta
    name = u'⑨的翅膀'
    image = gres.card_icewing
    image_small = gres.card_icewing_small
    is_action_valid = equip_iav

class IceWingSkill:
    # Skill
    name = u'⑨的翅膀'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class GrimoireCard:
    # action_stage meta
    name = u'魔导书'
    image = gres.card_grimoire
    image_small = gres.card_grimoire_small

    is_action_valid = equip_iav

class GrimoireSkill:
    # Skill
    name = u'魔导书'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[0]
            if isinstance(act, actions.ActionStage):
                if me.tags.get('attack_num', 0):
                    return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, source, target_list):
        skill = cl[0]
        assert skill.is_card(cards.GrimoireSkill)
        acards = skill.associated_cards
        if not (len(acards)) == 1:
            return (False, u'请选择一张牌')
        else:
            s = skill.lookup_tbl[acards[0].suit].ui_meta.name
            return (True, u'发动【%s】' % s)

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        #target = act.target_list[0]
        return u'Grimoire!'

class DollControlCard:
    # action_stage meta
    name = u'人形操控'
    image = gres.card_dollcontrol

    def is_action_valid(g, cl, source, tl):
        n = len(tl)
        if n == 0:
            return (False, u'请选择被控者')

        if tl[0] is source:
            return (False, u'你不可以控制你自己')

        if all(e.equipment_category != 'weapon' for e in tl[0].equips):
            return (False, u'被控者没有武器！')

        if n == 1:
            return (False, u'请选择被控者的攻击目标')
        elif n == 2:
            from .. import actions, cards
            c = cards.AttackCard()
            lc = actions.LaunchCard(tl[0], [tl[1]], c)
            if not lc.can_fire():
                return (False, u'被控者无法向目标出【击】！')
            return (True, u'乖，听话！')

class DollControl:
    # choose card meta
    text_valid = u'那好吧…'
    text = u'请出【击】（否则你的武器会被拿走）'

# -----END CARDS UI META-----

# -----BEGIN CHARACTERS UI META-----
__metaclass__ = gen_metafunc(characters)

class Parsee:
    # Character
    char_name = u'水桥帕露西'
    port_image = gres.parsee_port

class Envy:
    # Skill
    name = u'嫉妒'

    def clickable(game):
        me = game.me
        if me.stage == game.ACTION_STAGE and me.cards: # FIXME: lit on 'choose_card'
            return True
        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.Envy)
        if len(skill.associated_cards) != 1:
            return (False, u'请选择一张牌！')
        else:
            return cards.DemolitionCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|r发动了嫉妒技能，将|c208020ff%s|r当作|c208020ff%s|r对|c208020ff【%s】|r使用。' % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            target.ui_meta.char_name,
        )
        return s

# ----------

class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = gres.youmu_port

class Mijincihangzhan:
    # Skill
    name = u'迷津慈航斩'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

# ----------

class Koakuma:
    # Character
    char_name = u'小恶魔'
    port_image = gres.koakuma_port

class Find:
    # Skill
    name = u'寻找'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True
        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.Find)
        if not len(skill.associated_cards):
            return (False, u'请选择需要换掉的牌！')

        if not [g.me] == target_list:
            return (False, 'BUG!!')

        return (True, u'换掉这些牌')

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|r发动了寻找技能，换掉了%d张牌。' % (
            source.ui_meta.char_name,
            len(card.associated_cards),
        )
        return s

# -----END CHARACTERS UI META-----

# -----BEGIN TAGS UI META-----
tags = {}
def tag_metafunc(clsname, bases, _dict):
    data = DataHolder.parse(_dict)
    tags[clsname] = data

__metaclass__ = tag_metafunc

class attack_num:
    tag_anim = gres.tag_attacked
    display = lambda val: val <= 0

class wine:
    tag_anim = gres.tag_wine
    display = lambda val: val
# -----END TAGS UI META-----
