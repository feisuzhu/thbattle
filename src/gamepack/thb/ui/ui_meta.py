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

class UseHeal:
    # choose_card meta
    text_valid = u'神说，你不能在这里MISS'
    text = u'请选择一张【麻薯】…'

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
    name = u'弹幕'

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择弹幕的目标')

        if g.me is target_list[0]:
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

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
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
        s = u'|c208020ff【%s】|r发动了冈格尼尔之枪，将两张牌当作|c208020ff【弹幕】|r对|c208020ff【%s】|r使用。' % (
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
            return (False, u'请选择你的最后一张【弹幕】！')
        else:
            if not target_list:
                return (False, u'请选择弹幕的目标（最多可以选择3名玩家）')

            if g.me in target_list:
                return (True, u'您真的要自残么？！')
            else:
                return (True, u'觉醒吧，禁忌的炎之魔剑！')

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|Laevatein!...|c208020ff【弹幕】|r对|c208020ff【%s】|r使用。' % (
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
        return (True, u'\腋/！')

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
        # for effects.launch_effect
        source = act.source
        card = act.card
        #target = act.target_list[0]
        return u'Grimoire!'

class DollControlCard:
    # action_stage meta
    name = u'人形操控'
    image = gres.card_dollcontrol

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
            from .. import actions, cards
            c = cards.AttackCard()
            lc = actions.LaunchCard(tl[0], [tl[1]], c)
            if not lc.can_fire():
                return (False, u'被控者无法向目标出【弹幕】！')
            return (True, u'乖，听话！')

class DollControl:
    # choose card meta
    text_valid = u'那好吧…'
    text = u'请出【弹幕】（否则你的武器会被拿走）'

class DonationBoxCard:
    # action_stage meta
    name = u'塞钱箱'
    image = gres.card_donationbox

    def is_action_valid(g, cl, tl):
        n = len(tl)
        if not n:
            return (False, u'请选择1-2名玩家')

        if g.me in tl:
            return (True, u'你不能选择自己作为目标')

        for t in tl:
            if not (t.cards or t.showncards or t.equips):
                return (False, u'目标没有可以给你的牌')

        return (True, u'纳奉！纳奉！')

class DonationBox:
    # choose card meta
    text_valid = u'这是抢劫啊！'
    text = u'请选择一张牌（否则会随机选择一张）'


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

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.Envy)
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.suit not in (cards.Card.SPADE, cards.Card.CLUB):
                return (False, u'请选择一张黑色的牌！')
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
        if me.tags.get('find_tag', 0) >= me.tags.get('turn_count', 0):
            return False

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

# ----------

class Marisa:
    # Character
    char_name = u'雾雨魔理沙'
    port_image = gres.marisa_port

class Borrow:
    # Skill
    name = u'借走'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class BorrowHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【借走】技能吗？'

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'请选择1-2名玩家')

        return (True, u'哎哎，什么还不还的~')

# ----------

class Daiyousei:
    # Character
    char_name = u'大妖精'
    port_image = gres.daiyousei_port

class SupportSkill:
    # Skill
    name = u'支援'

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
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        if len(target_list) != 1: return (False, u'请选择1名玩家')
        return (True, u'加油！')

    def effect_string(act):
        # for effects.launch_effect
        s = u'daiyousei support'
        return s

class Moe:
    # Skill
    name = u'卖萌'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

# ----------

class Flandre:
    # Character
    char_name = u'芙兰朵露'
    port_image = gres.flandre_port

class CriticalStrike:
    # Skill
    name = u'狂咲'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class CriticalStrikeHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【狂咲】吗？'

# ----------

class Alice:
    # Character
    char_name = u'爱丽丝'
    port_image = gres.alice_port

class DollManipulation:
    # Skill
    name = u'人形操演'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

# ----------

class Nazrin:
    # Character
    char_name = u'娜兹琳'
    port_image = gres.nazrin_port

class TreasureHuntSkill:
    # Skill
    name = u'探宝'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class TreasureHuntHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【探宝】吗？'

class Agile:
    # Skill
    name = u'轻敏'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, cards.UseGraze) and (me.cards or me.showncards):
            return True

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.suit not in (cards.Card.SPADE, cards.Card.CLUB):
                return (False, u'请选择一张黑色的牌！')
            return (True, u'这种三脚猫的弹幕，想要打中我是不可能的啦~')

    def effect_string(act):
        # for effects.launch_effect
        s = u'nazrin agile'
        return s

# ----------

class Yugi:
    # Character
    char_name = u'星熊勇仪'
    port_image = gres.yugi_port

class AssaultSkill:
    # Skill
    name = u'强袭'

    def clickable(game):
        me = game.me
        if me.tags.get('yugi_assault', 0) >= me.tags.get('turn_count', 0):
            return False
        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        return isinstance(act, actions.ActionStage)

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择强袭的目标，以及一张武器牌（不选自己会受到1点伤害）')

        if g.me is target_list[0]:
            return (False, u'不可以对自己发动')
        else:
            return (True, u'[不知道该说什么，先这样吧]')

    def effect_string(act):
        # for effects.launch_effect
        s = u'yugi assault'
        return s

class FreakingPowerSkill:
    # Skill
    name = u'怪力'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class YugiHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【怪力】吗？'

# ----------

class Library:
    # Skill
    name = u'图书'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Knowledge:
    # Skill
    name = u'博学'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Patchouli:
    # Character
    char_name = u'帕秋莉'
    port_image = gres.patchouli_port

# ----------

class Luck:
    # Skill
    name = u'幸运'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Tewi:
    # Character
    char_name = u'因幡帝'
    port_image = gres.tewi_port

# ----------

class SealingArraySkill:
    # Skill
    name = u'封魔阵'
    image = gres.card_sealarray
    tag_anim = gres.tag_sealarray


    def clickable(game):
        me = game.me

        if me.tags.get('reimusa_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.suit != cards.Card.DIAMOND:
                return (False, u'请选择一张方片花色的牌！')
            return (True, u'乖，歇会吧~')

    def effect_string(act):
        # for effects.launch_effect
        return u'reimu sa'
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u''
        return s

class Flight:
    # Skill
    name = u'飞行'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class TributeTarget:
    # Skill
    name = u'纳奉'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Tribute:
    # Skill
    name = u'塞钱'

    def clickable(game):
        me = game.me

        if me.tags.get('tribute_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, tl):
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        if len(cl) != 1: return (False, u'只能选择一张牌')
        if len(tl) != 1 or not tl[0].has_skill(characters.TributeTarget):
            return (False, u'请选择一只灵梦')
        return (True, u'塞钱……会发生什么呢？')

    def effect_string(act):
        # for effects.launch_effect
        s = u'reimu tribute'
        return s

class Reimu:
    # Character
    char_name = u'博丽灵梦'
    port_image = gres.reimu_port

# ----------

class Jolly:
    # Skill
    name = u'愉快'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class SurpriseSkill:
    # Skill
    name = u'惊吓'

    def clickable(game):
        me = game.me

        if me.tags.get('surprise_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards):
            return True

        return False

    def is_action_valid(g, cl, tl):
        if len(tl) != 1:
            return (False, u'请选择惊吓对象…')
        #return (True, u'(´・ω・`)')
        return (True, u'\ ( °▽ °) /')
        #return (True, u'SURPRISE！')

    def effect_string(act):
        # for effects.launch_effect
        s = u'surprise'
        return s

class Surprise:
    # choose_option
    choose_option_buttons = (
        (u'黑桃', cards.Card.SPADE),
        (u'红桃', cards.Card.HEART),
        (u'草花', cards.Card.CLUB),
        (u'方片', cards.Card.DIAMOND),
    )
    choose_option_prompt = u'请选择一个花色…'

class Kogasa:
    # Character
    char_name = u'多多良小伞'
    port_image = gres.kogasa_port

# ----------

class FirstAid:
    # Skill
    name = u'急救'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.UseHeal):
            return True

        return False

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择一张红色牌！')
        return (True, u'k看不到@#@#￥@#￥')

class Medic:
    # Skill
    name = u'医者'

    def clickable(game):
        me = game.me

        if me.tags.get('turn_count', 0) <= me.tags.get('medic_tag', 0):
            return False

        try:
            act = game.action_stack[0]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards):
            return True

        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        me = g.me
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张手牌！')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, u'只能使用手牌发动！')
        elif not tl or len(tl) != 1:
            return (False, u'请选择一名受伤的玩家')
        elif tl[0].maxlife <= tl[0].life:
            return (False, u'这只精神着呢，不用管她')
        return (True, u'少女，身体要紧啊！')

    def effect_string(act):
        # for effects.launch_effect
        s = u'medic'
        return s

class Eirin:
    # Character
    char_name = u'八意永琳'
    port_image = gres.eirin_port

# ----------

class Trial:
    # Skill
    name = u'审判'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Majesty:
    # Skill
    name = u'威严'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class TrialHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【审判】吗？'

    # choose_card
    text = u'请选择一张牌代替当前的判定牌'
    text_valid = u'有罪！'

class MajestyHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【威严】吗？'

class Shikieiki:
    # Character
    char_name = u'四季映姬'
    port_image = gres.shikieiki_port

# ----------

class Masochist:
    # Skill
    name = u'抖Ｍ'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class MasochistHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【抖Ｍ】吗？'

    # choose_card
    text = u'请选择你要给出的牌'
    text_valid = u'给你牌~'

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'给你牌~')

class Tenshi:
    # Character
    char_name = u'比那名居天子'
    port_image = gres.tenshi_port

# ----------

class FlowerQueen:
    # Skill
    name = u'花王'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[0]
            if isinstance(act, (actions.ActionStage, cards.UseAttack, cards.UseGraze, cards.DollControl)):
                return True
        except IndexError:
            pass
        return False

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        acards = skill.associated_cards
        if len(acards) != 1 or acards[0].suit != cards.Card.CLUB:
            return (False, u'请选择1张草花色手牌！')
        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for effects.launch_effect
        s = u'flower queen'
        return s

class MagicCannon:
    # Skill
    name = u'魔炮'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class PerfectKill:
    # Skill
    name = u'完杀'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Yuuka:
    # Character
    char_name = u'风见幽香'
    port_image = gres.yuuka_port

# ----------

class Darkness:
    # Skill
    name = u'黑暗'

    def clickable(game):
        me = game.me
        try:
            tags = me.tags
            if tags['turn_count'] <= tags['darkness_tag']:
                return False
            act = game.action_stack[0]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if not cl or len(cl) != 1:
            return (False, u'请选择一张牌')

        if not len(tl):
            return (False, u'请选择第一名玩家（先出弹幕）')
        elif len(tl) == 1:
            return (False, u'请选择第二名玩家（后出弹幕）')
        else:
            return (True, u'你们的关系…是~这样吗？')

    def effect_string(act):
        # for effects.launch_effect
        s = u'darkness duel'
        return s

class Cheating:
    # Skill
    name = u'作弊'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Rumia:
    # Character
    char_name = u'露米娅'
    port_image = gres.rumia_port

# ----------

class Netoru:
    # Skill
    name = u'寝取'

    def clickable(game):
        me = game.me
        try:
            if me.tags['netoru_tag'] >= me.tags['turn_count']:
                return False
            act = game.action_stack[0]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        me = g.me
        if not cl or len(cl) != 2:
            return (False, u'请选择两张手牌')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, u'只能使用手牌发动！')

        if len(tl) != 1:
            return (False, u'请选择一名受伤的玩家')

        t = tl[0]
        if t.life >= t.maxlife:
            return (False, u'这位少女节操满满，不会答应你的…')
        else:
            return (True, u'少女，做个好梦~')

    def effect_string(act):
        # for effects.launch_effect
        s = u'netoru'
        return s

class Psychopath:
    # Skill
    name = u'变态'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Rinnosuke:
    # Character
    char_name = u'森近霖之助'
    port_image = gres.rinnosuke_port

# ----------

class Fengshui:
    # Skill
    name = u'风水'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class ExtremeIntelligence:
    # Skill
    name = u'极智'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class FengshuiHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【风水】吗？'

class ExtremeIntelligenceHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【极智】吗？'

    # choose_card
    text = u'请选择1张牌弃置'
    text_valid = u'再来！'

class Ran:
    # Character
    char_name = u'八云蓝'
    port_image = gres.ran_port

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
