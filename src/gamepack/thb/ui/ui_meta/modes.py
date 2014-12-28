# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict

# -- third party --
# -- own --
from .common import gen_metafunc, meta_property
from gamepack.thb import thb2v2, thb3v3, thbbook, thbdebug, thbfaith, thbidentity, thbkof

# -----BEGIN THB3v3 UI META-----
__metaclass__ = gen_metafunc(thb3v3)


class THBattle:
    name = u'符斗祭 - 3v3'
    logo = 'thb-modelogo-3v3'
    description = (
        u'|R游戏人数|r：6人\n'
        u'\n'
        u'阵营分为|!B博丽|r和|!O守矢|r，每个阵营3名玩家，交错入座。\n'
        u'由ROLL点最高的人开始，按照顺时针1-2-2-1的方式选将。\n'
        u'选将完成由ROLL点最高的玩家开始行动。\n'
        u'ROLL点最高的玩家开局摸3张牌，其余玩家开局摸4张牌。\n'
        u'\n'
        u'|R胜利条件|r：击坠所有对方阵营玩家。'
    )
    params_disp = {
        'random_seat': {
            'desc': u'随机座位阵营',
            'options': [
                (u'固定', False),
                (u'随机', True),
            ],
        },
    }

    def ui_class():
        from gamepack.thb.ui.view import THBattleUI
        return THBattleUI

    T = thb3v3.Identity.TYPE
    identity_table = {
        T.HIDDEN: u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA: u'守矢'
    }

    identity_color = {
        T.HIDDEN: u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA: u'orange'
    }

    del T

# -----END THB3v3 UI META-----


# -----BEGIN THBKOF UI META-----
__metaclass__ = gen_metafunc(thbkof)


class THBattleKOF:
    name = u'符斗祭 - KOF模式'
    logo = 'thb-modelogo-kof'
    description = (
        u'|R游戏人数|r：2人\n'
        u'\n'
        u'|R选将模式|r：选将按照1-2-2-2-2-1来选择。\n'
        u'\n'
        u'|R决定出场顺序|r：选好角色后，进行排序。拖动角色可以进行排序，左边3名为出场角色，越靠左的最先出场（注意：当把一个角色拖到另一个角色左边时，靠右的角色会被顶下去）\n'
        u'\n'
        u'|R游戏过程|r：选好角色后，将会翻开第一个角色进行对决，其他角色为隐藏，中途不能调换顺序。当有一方角色MISS后，需弃置所有的牌（手牌、装备牌、判定区的牌），然后翻开下一个角色，摸4张牌。\n'
        u'\n'
        u'|R胜利条件|r：当其中一方3名角色全部MISS，判对方胜出'
    )

    params_disp = {
        'no_imba': {
            'desc': u'不平衡角色',
            'options': [
                (u'禁用', True),
                (u'允许', False),
            ],
        },
    }

    def ui_class():
        from gamepack.thb.ui.view import THBattleKOFUI
        return THBattleKOFUI

    T = thbkof.Identity.TYPE
    identity_table = {
        T.HIDDEN:  u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA:  u'守矢'
    }

    identity_color = {
        T.HIDDEN:  u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA:  u'orange'
    }

    del T

# -----END THB3v3 UI META-----


# -----BEGIN THBIdentity UI META-----
__metaclass__ = gen_metafunc(thbidentity)


class THBattleIdentity:
    name = u'符斗祭 - 标准8人身份场'
    logo = 'thb-modelogo-8id'
    description = (
        u'|R游戏人数|r：8人\n'
        u'\n'
        u'|R身份分配|r：1|!RBOSS|r、2|!O道中|r、1|!G黑幕|r、4|!B城管|r\n'
        u'\n'
        u'|!RBOSS|r：|!RBOSS|r的体力上限+1。游戏开局时展示身份。胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        u'\n'
        u'|!O道中|r：胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        u'\n'
        u'|!B城管|r：胜利条件为击坠|!RBOSS|r。当|!B城管|rMISS时，击坠者摸3张牌。\n'
        u'\n'
        u'|!G黑幕|r：胜利条件为在除了|!RBOSS|r的其他人都MISS的状况下击坠|!RBOSS|r。\n'
        u'\n'
        u'玩家的身份会在MISS后公开。|!RBOSS|r的身份会在开局的时候公开。'
    )
    params_disp = {
        'double_curtain': {
            'desc': u'双黑幕',
            'options': [
                (u'禁用', False),
                (u'启用', True),
            ],
        },
    }

    def ui_class():
        from gamepack.thb.ui.view import THBattleIdentityUI
        return THBattleIdentityUI

    T = thbidentity.Identity.TYPE
    identity_table = {
        T.HIDDEN:     u'？',
        T.ATTACKER:   u'城管',
        T.BOSS:       u'BOSS',
        T.ACCOMPLICE: u'道中',
        T.CURTAIN:    u'黑幕',
    }

    identity_color = {
        T.HIDDEN:     u'blue',
        T.ATTACKER:   u'blue',
        T.BOSS:       u'red',
        T.ACCOMPLICE: u'orange',
        T.CURTAIN:    u'green',
    }

    del T

# -----END THBIdentity UI META-----


# -----BEGIN THBFaith UI META-----
__metaclass__ = gen_metafunc(thbfaith)


class THBattleFaith:
    name = u'符斗祭 - 信仰争夺战'
    logo = 'thb-modelogo-faith'
    description = (
        u'|R游戏人数|r：6人\n'
        u'\n'
        u'|G游戏开始|r：游戏开始时，随机向在场玩家分配6张身份牌：3|!B博丽|r，3|!O守矢|r，双方对立。若出现同一方阵营座次连续三人的情况，则第三人须与下一名座次的玩家交换身份牌。\n'
        u'\n'
        u'|G选将阶段|r：共发给每人4张角色牌，其中一张为暗置。每名玩家选择其中一张作为出场角色，再选择一张作为备用角色（不得查看暗置角色牌）。将三张备用角色牌置于一旁作为备用角色。\n'
        u'\n'
        u'|G游戏开始|r：游戏开始时，所有角色摸4张牌，此时除首先行动的玩家均可以进行一次弃置4张牌并重新摸4张牌的操作。\n'
        u'\n'
        u'|G玩家死亡|r：当一名玩家死亡时，改玩家需弃置其所有的牌，然后弃置该玩家全部区域内的牌。从剩余的备用角色中选择一名作为出场角色并明示之，之后摸4张牌。此时该角色可以弃置全部的4张牌并重新摸4张牌。玩家死亡不执行任何奖惩。\n'
        u'\n'
        u'|G胜负条件|r：当一方死亡角色数到达三名，或投降时，该方判负。'
    )
    params_disp = {
        'random_seat': {
            'desc': u'随机座位阵营',
            'options': [
                (u'随机', True),
                (u'固定', False),
            ],
        },
    }

    def ui_class():
        from gamepack.thb.ui.view import THBattleFaithUI
        return THBattleFaithUI

    T = thbfaith.Identity.TYPE
    identity_table = {
        T.HIDDEN:  u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA:  u'守矢'
    }

    identity_color = {
        T.HIDDEN:  u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA:  u'orange'
    }

    del T


class DeathHandler:  # noqa
    # choose_option
    choose_option_buttons = ((u'全部换走', True), (u'不用换', False))
    choose_option_prompt  = u'你要将摸到的牌全部换掉吗？'

# -----END THBFaith UI META-----

# -----BEGIN THB2v2 UI META-----
__metaclass__ = gen_metafunc(thb2v2)


class THBattle2v2:
    name = u'符斗祭 - 2v2'
    logo = 'thb-modelogo-2v2'
    description = (
        u'|R游戏人数|r：4人\n'
        u'\n'
        u'|G座次|r：\n'
        u'创建房间时可选固定阵容或随机阵容。\n'
        u'Roll点，由点数最高的玩家为1号位，然后对面点数最大的为2号位，按1-2-2-1的顺序逆时针行动。\n'
        u'\n'
        u'|G选将|r：\n'
        u'从角色堆里选出20名角色，由1号位开始，每人选择Ban掉其中一个角色。\n'
        u'每人随机从剩下的卡牌中获得4张角色卡作为备选（其中一张为阿卡林）\n'
        u'玩家可以选择其中一名角色进行游戏\n'
        u'\n'
        u'|G行动和胜利条件|r：\n'
        u'选择角色完毕后，每人摸4张牌。由一号位开始逆时针行动。\n'
        u'一名角色阵亡后，队友可以选择获得其所有牌或摸两张牌。\n'
        u'当一方所有的角色都阵亡时，游戏结束，另一方获胜。\n'
    )

    params_disp = OrderedDict((
        ('random_force', {
            'desc': u'随机阵营',
            'options': [
                (u'随机', True),
                (u'固定', False),
            ],
        }),
        ('draw_extra_card', {
            'desc': u'摸牌数量',
            'options': [
                (u'2张', False),
                (u'3张', True),
            ],
        }),
    ))

    def ui_class():
        from gamepack.thb.ui.view import THBattle2v2UI
        return THBattle2v2UI

    T = thb2v2.Identity.TYPE
    identity_table = {
        T.HIDDEN:  u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA:  u'守矢'
    }

    identity_color = {
        T.HIDDEN:  u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA:  u'orange'
    }

    del T


class HeritageHandler:
    # choose_option
    choose_option_buttons = ((u'获取队友的所有牌', 'inherit'), (u'摸两张牌', 'draw'))
    choose_option_prompt  = u'队友MISS，请选择你的动作'

# -----END THB2v2 UI META-----

__metaclass__ = gen_metafunc(thbdebug)


# -----BEGIN THBDebug UI META-----
class DebugUseCard:
    # Skill
    name = u'转化'
    params_ui = 'UIDebugUseCardSelection'

    @meta_property
    def image(c):
        return c.treat_as.ui_meta.image

    @meta_property
    def image_small(c):
        return c.treat_as.ui_meta.image_small

    description = u'DEBUG'

    def clickable(game):
        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        try:
            skill.treat_as.ui_meta
        except:
            return False, u'Dummy'

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def is_complete(g, cl):
        return True, u'XXX'


class DebugDecMaxLife:
    # Skill
    name = u'减上限'

    def clickable(g):
        return True

    def is_action_valid(g, cl, target_list):
        acards = cl[0].associated_cards
        if len(acards):
            return (False, u'请不要选择牌！')

        return (True, u'XXX')
# -----END THBDebug UI META-----


# -----BEGIN THBBook UI META-----
__metaclass__ = gen_metafunc(thbbook)


class THBattleBook:
    name = u'符斗祭 - 抢书大作战'
    logo = 'thb-modelogo-book'
    params_disp = {}
    description = (
        u'|R游戏人数|r：4人+1NPC\n'
        u'\n'
        u'|G游戏目标|r：我方势力拿到尽量多的书\n'
        u'\n'
        u'|G游戏开始|r：\n'
        u'|B|R>> |r游戏开始时，|G【小恶魔】|r会获得7个书的标记，体力和体力上限+4\n'
        u'|B|R>> |r玩家按照势力以AABB的方式排座位，由|G【小恶魔】|r先出牌\n'
        u'|B|R>> |r所有玩家摸4张牌。\n'
        u'\n'
        u'|G书的取得|r：\n'
        u'|B|R>> |r你对任意角色造成伤害后，可以获得造成伤害数量的书。\n'
        u'|B|R>> |r若该角色被你击坠，你获得该角色的所有书。\n'
        u'|B|R>> |r若该角色受到自己/无来源的伤害导致MISS，|G【小恶魔】|r获得该角色的所有书。\n'
        u'\n'
        u'|G击坠结算|r：MISS的角色在轮到自己回合的时候重新回到场上，体力值回复2点，摸2张牌，并跳过所有阶段。\n'
        u'\n'
        u'|G胜利条件|r：\n'
        u'|B|R>> |r|G【小恶魔】|rMISS，此时持有书的数量多的势力胜利。\n'
        u'|B|R>> |r有势力拿到所有的书，此时该势力胜利。\n'
        u'\n'
        u'|G小恶魔的行动|r：\n'
        u'|B|R>> |r不会装备绿色UFO。\n'
        u'|B|R>> |r会选择目前持有书最多的角色攻击，若此时有多于1名角色，会选择体力最多的角色攻击。若没有角色有书，则不做攻击。\n'
        u'|B|R>> |r若无法攻击选定的目标，则不做攻击。\n'
        u'|B|R>> |r不受延时符卡影响。\n'
    ).strip()

    def ui_class():
        from gamepack.thb.ui.view import THBattleBookUI
        return THBattleBookUI

    T = thbbook.Identity.TYPE
    identity_table = {
        T.HIDDEN:  u'？',
        T.HAKUREI: u'博丽',
        T.MORIYA:  u'守矢',
        T.ADMIN:   u'管理员',
    }

    identity_color = {
        T.HIDDEN:  u'blue',
        T.HAKUREI: u'blue',
        T.MORIYA:  u'orange',
        T.ADMIN:   u'red',
    }

    del T


class BookTransferHandler:  # noqa
    # choose_option
    choose_option_buttons = ((u'获得书', True), (u'留在原处', False))
    choose_option_prompt  = u'你要获得对方的书吗？'


class GrabBooks:
    def effect_string(act):
        return u'|G【%s】|r抢走了|G【%s】|r的%d本书。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.amount,
        )

# -----END THBFaith UI META-----
