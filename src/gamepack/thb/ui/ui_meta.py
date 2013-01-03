# -*- coding: utf-8 -*-
from .. import actions
from .. import cards
from .. import characters
from .. import thb3v3, thbidentity, thbkof

from game.autoenv import Game
G = Game.getgame

import types
import resource as gres
from client.ui import resource as cres

from utils import DataHolder, BatchList
from types import FunctionType

metadata = {}


class UIMetaAccesser(object):
    def __init__(self, obj, cls):
        self.obj = obj
        self.cls = cls

    def __getattr__(self, name):
        cls = self.cls
        if hasattr(cls, '_is_mixedclass'):
            l = list(cls.__bases__)
        else:
            l = [cls]

        while l:
            c = l.pop(0)
            try:
                val = metadata[c][name]

                if isinstance(val, FunctionType) and getattr(val, '_is_property', False):
                    val = val(self.obj or self.cls)

                return val

            except KeyError:
                pass
            b = c.__base__
            if b is not object: l.append(b)
        raise AttributeError('%s.%s' % (self.cls.__name__, name))


class UIMetaDescriptor(object):
    def __get__(self, obj, cls):
        return UIMetaAccesser(obj, cls)


def gen_metafunc(_for):
    def metafunc(clsname, bases, _dict):
        meta_for = getattr(_for, clsname)
        meta_for.ui_meta = UIMetaDescriptor()
        if meta_for in metadata:
            raise Exception('%s ui_meta redefinition!' % meta_for)

        metadata[meta_for] = _dict

    return metafunc


def property(f):
    f._is_property = True
    return f

# -----COMMON FUNCTIONS-----
def my_turn(g):
    me = g.me

    try:
        act = g.action_stack[-1]
    except IndexError:
        return False

    if not isinstance(act, actions.ActionStage):
        return False

    if act.target is not g.me: return False

    return True

# -----END COMMON FUNCTIONS-----

# -----BEGIN THB3v3 UI META-----
__metaclass__ = gen_metafunc(thb3v3)

class ActFirst:
    # choose_option meta
    choose_option_buttons = ((u'先出牌', True), (u'弃权', False))
    choose_option_prompt = u'你要首先出牌吗（可以转让给己方阵营的其他玩家）？'

class THBattle:
    name = u'符斗祭 - 3v3 - 休闲'
    logo = gres.thblogo_3v3

    from .view import THBattleUI as ui_class

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
    logo = gres.thblogo_kof

    from .view import THBattleKOFUI as ui_class

    T = thbkof.Identity.TYPE
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

# -----BEGIN THBIdentity UI META-----
__metaclass__ = gen_metafunc(thbidentity)

class THBattleIdentity:
    name = u'符斗祭 - 标准8人身份场'
    logo = gres.thblogo_8id

    from .view import THBattleIdentityUI as ui_class

    T = thbidentity.Identity.TYPE
    identity_table = {
        T.HIDDEN: u'？',
        T.ATTACKER: u'城管',
        T.BOSS: u'BOSS',
        T.ACCOMPLICE: u'道中',
        T.CURTAIN: u'黑幕',
    }

    identity_color = {
        T.HIDDEN: u'blue',
        T.ATTACKER: u'blue',
        T.BOSS: u'red',
        T.ACCOMPLICE: u'orange',
        T.CURTAIN: u'green',
    }

    del T

class THBattleIdentity5:
    name = u'符斗祭 - 标准5人身份场'
    logo = gres.thblogo_5id

    from .view import THBattleIdentity5UI as ui_class

    T = thbidentity.Identity.TYPE
    identity_table = {
        T.HIDDEN: u'？',
        T.ATTACKER: u'城管',
        T.BOSS: u'BOSS',
        T.ACCOMPLICE: u'道中',
        T.CURTAIN: u'黑幕',
    }

    identity_color = {
        T.HIDDEN: u'blue',
        T.ATTACKER: u'blue',
        T.BOSS: u'red',
        T.ACCOMPLICE: u'orange',
        T.CURTAIN: u'green',
    }

    del T

# -----END THBIdentity UI META-----


# -----BEGIN ACTIONS UI META-----
__metaclass__ = gen_metafunc(actions)


class DropCardStage:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'OK，就这些了')
        else:
            return (False, u'请弃掉%d张牌…' % act.dropn)

    def effect_string(act):
        if act.dropn > 0:
            return u'|G【%s】|r弃掉了%d张牌。' % (
                act.target.ui_meta.char_name, act.dropn
            )

class Damage:
    def effect_string(act):
        s, t = act.source, act.target
        if s:
            return u'|G【%s】|r对|G【%s】|r造成了%d点伤害。' % (
                s.ui_meta.char_name, t.ui_meta.char_name, act.amount
            )
        else:
            return u'|G【%s】|r受到了%d点无来源的伤害。' % (
                t.ui_meta.char_name, act.amount
            )


class LifeLost:
    def effect_string(act):
        return u'|G【%s】|r流失了%d点体力。' % (
            act.target.ui_meta.char_name, act.amount
        )


class LaunchCard:
    def effect_string_before(act):
        s, tl = act.source, BatchList(act.target_list)
        c = act.card
        from ..cards import Skill
        if isinstance(c, Skill):
            return c.ui_meta.effect_string(act)
        elif c:
            return u'|G【%s】|r对|G【%s】|r使用了|G%s|r。' % (
                s.ui_meta.char_name,
                u'】|r、|G【'.join(tl.ui_meta.char_name),
                act.card.ui_meta.name
            )

    def ray(act):
        if getattr(act.card.ui_meta, 'custom_ray', False):
            return []

        s = act.source
        return [(s, t) for t in act.target_list]


class PlayerDeath:
    barrier = True
    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|rMISS了。' % (
            tgt.ui_meta.char_name,
        )


C = cards.Card
ftstring = {
    C.SPADE: u'|r|B[黑桃 ',
    C.HEART: u'|r|R|B[红桃 ',
    C.CLUB: u'|r|B[草花 ',
    C.DIAMOND: u'|r|R|B[方片 ',
}
del C

def card_suitnum(c):
    suit = ftstring.get(c.suit, u'|r[错误 ')
    num = ' A23456789_JQK'[c.number]
    if num == '_': num = '10'
    return suit + num + ']|r'

class Fatetell:
    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|r进行了一次判定，判定结果为%s' % (
            tgt.ui_meta.char_name,
            card_suitnum(act.card)
        )


class TurnOverCard:
    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|r翻开了牌堆顶的一张牌，%s' % (
            tgt.ui_meta.char_name,
            card_suitnum(act.card)
        )


class RevealIdentity:
    def effect_string(act):
        g = Game.getgame()
        me = g.me
        if not (me in act.to if isinstance(act.to, list) else me is act.to):
            return

        tgt = act.target
        i = tgt.identity
        try:
            name = u'|G%s|r' % tgt.ui_meta.char_name
        except:
            name = u'|R%s|r' % tgt.account.username

        return u'%s的身份是：|R%s|r' % (
            name,
            Game.getgame().ui_meta.identity_table[i.type],
        )

class Pindian:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'不服来战！')
        else:
            return (False, u'请选择一张牌用于拼点')

    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r发起了拼点' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        winner = act.source if act.succeeded else act.target
        return u'|G【%s】|r是人生赢家！' % (
            winner.ui_meta.char_name
        )

# -----END ACTIONS UI META-----

# -----BEGIN CARDS UI META-----
__metaclass__ = gen_metafunc(cards)

class DelayedLaunchCard:
    def effect_string_before(act):
        s, t = act.source, act.target
        c = act.card
        from ..cards import Skill
        if isinstance(c, Skill):
            return c.ui_meta.effect_string(act)
        elif c:
            return u'|G【%s】|r对|G【%s】|r使用了|G%s|r。' % (
                s.ui_meta.char_name,
                t.ui_meta.char_name,
                act.card.ui_meta.name
            )


class HiddenCard:
    # action_stage meta
    image = gres.card_hidden
    name = u'这个是隐藏卡片，你不应该看到它'

    def is_action_valid(g, cl, target_list):
        return (False, u'这是BUG，你没法发动这张牌…')

class AttackCard:
    # action_stage meta
    image = gres.card_attack
    name = u'弹幕'
    description = (
        u'|R弹幕|r\n\n'
        u'你的出牌阶段，对除你外，你攻击范围内的一名角色使用，效果是对该角色造成1点伤害。\n'
        u'|B|R>> |r游戏开始时你的攻击范围是1。\n'
        u'|B|R>> |r每个出牌阶段你只能使用一张【弹幕】。'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择弹幕的目标')

        return (True, u'来一发！')


class FreeAttackSkill:
    # Skill
    name = u'无限弹幕'


class GrazeCard:
    # action_stage meta
    name = u'擦弹'
    image = gres.card_graze
    description = (
        u'|R擦弹|r\n\n'
        u'当你受到【弹幕】的攻击时，你可以使用一张【擦弹】来抵消【弹幕】的效果。\n'
        u'|B|R>> |r【擦弹】通常情况下只能在回合外使用或打出。\n'
    )

    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动使用擦弹')

class WineCard:
    # action_stage meta
    name = u'酒'
    image = gres.card_wine
    description = (
        u'|R酒|r\n\n'
        u'使用后获得|B喝醉|r状态。\n'
        u'|B喝醉|r状态下，使用【弹幕】命中后伤害+1，受到致命伤害时伤害-1。\n'
        u'|B|R>> |r效果触发或者轮到自己的行动回合时须弃掉|B喝醉|r状态。'
    )

    def is_action_valid(g, cl, target_list):
        if g.me.tags.get('wine', False):
            return (True, u'你已经醉了，还要再喝吗？')
        return (True, u'青岛啤酒，神主也爱喝！')

class Wine:
    def effect_string(act):
        return u'|G【%s】|r喝醉了…' % act.target.ui_meta.char_name

class WineRevive:
    def effect_string(act):
        return u'|G【%s】|r醒酒了。' % act.target.ui_meta.char_name

class ExinwanCard:
    # action_stage meta
    name =u'恶心丸'
    image = gres.card_exinwan
    description = (
        u'|R恶心丸|r\n\n'
        u'当该牌以任意的方式由手牌/明牌区进入弃牌堆时，引发弃牌动作的玩家需要选择其中一项执行：\n'
        u'|B|R>> |r受到一点伤害，无来源\n'
        u'|B|R>> |r弃两张牌'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'哼，哼，哼哼……')

class ExinwanHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'节操给你，离我远点！')
        else:
            return (False, u'请选择两张牌（不选则受到一点无源伤害）')

class UseGraze:
    # choose_card meta
    image = gres.card_graze
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'我闪！')
        else:
            return (False, u'请打出一张【擦弹】…')

    def effect_string(act):
        if not act.succeeded: return None
        t = act.target
        return u'|G【%s】|r打出了|G%s|r。' % (
            t.ui_meta.char_name,
            act.cards[0].ui_meta.name,
        )

class LaunchGraze:
    # choose_card meta
    image = gres.card_graze
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'我闪！')
        else:
            return (False, u'请使用一张【擦弹】抵消【弹幕】效果…')

    def effect_string(act):
        if not act.succeeded: return None
        t = act.target
        return u'|G【%s】|r使用了|G%s|r。' % (
            t.ui_meta.char_name,
            act.cards[0].ui_meta.name,
        )

class UseAttack:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'打架？来吧！')
        else:
            return (False, u'请打出一张弹幕…')

    def effect_string(act):
        if not act.succeeded: return None
        t = act.target
        return u'|G【%s】|r打出了|G%s|r。' % (
            t.ui_meta.char_name,
            act.cards[0].ui_meta.name,
        )

class HealCard:
    # action_stage meta
    image = gres.card_heal
    name = u'麻薯'
    description = (
        u'|R麻薯|r\n\n'
        u'【麻薯】能在两种情况下使用：\n'
        u'1、在你的出牌阶段，你可以使用它来回复你的1点体力。\n'
        u'2、当有角色处于濒死状态时，你可以对该角色使用【麻薯】，防止该角色的死亡。\n'
        u'|B|R>> |r出牌阶段，若你没有损失体力，你不可以对自己使用【麻薯】。'
    )

    def is_action_valid(g, cl, target_list):
        target = target_list[0]

        if target.life >= target.maxlife:
            return (False, u'您已经吃饱了')
        else:
            return (True, u'来一口，精神焕发！')

class UseHeal:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'神说，你不能在这里MISS')
        else:
            return (False, u'请选择一张【麻薯】…')

class Heal:
    def effect_string(act):
        if act.succeeded:
            return u'|G【%s】|r回复了%d点体力。' % (
                act.target.ui_meta.char_name, act.amount
            )

class DemolitionCard:
    # action_stage meta
    image = gres.card_demolition
    name = u'城管执法'
    description = (
        u'|R城管执法|r\n\n'
        u'出牌阶段对(除自己外)任意一名玩家使用，随机抽取并弃掉对方一张手牌，或选择并弃掉一张对方面前的牌(包括装备、明牌区和判定区内延时类符卡)。'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择拆除目标')

        target= target_list[0]
        if not len(target.cards) + len(target.showncards) + len(target.equips) + len(target.fatetell):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'嗯，你的牌太多了')

class Demolition:
    def effect_string(act):
        if not act.succeeded: return None
        return u'|G【%s】|r卸掉了|G【%s】|r的|G%s|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.card.ui_meta.name,
        )

class RejectCard:
    # action_stage meta
    name = u'好人卡'
    image = gres.card_reject
    description = (
        u'|R好人卡|r\n\n'
        u'目标符卡对目标角色生效前，对目标符卡使用。抵消该符卡对其指定的一名目标角色产生的效果。'
    )
    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动出好人卡')

class RejectHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        from ..cards import Reject
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

class Reject:
    def effect_string_before(act):
        return u'|G【%s】|r为|G【%s】|r受到的|G%s|r使用了|G%s|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.target_act.associated_card.ui_meta.name,
            act.associated_card.ui_meta.name,
        )

    def ray(act):
        return [(act.source, act.target)]


class SealingArrayCard:
    # action_stage meta
    name = u'封魔阵'
    image = gres.card_sealarray
    tag_anim = lambda c: gres.tag_sealarray
    description = (
        u'|R封魔阵|r\n\n'
        u'延时类符卡\n'
        u'出牌阶段对任意一名玩家使用,将此牌置于目标玩家判定区,对方在其判定阶段需判定——如果判定结果为红桃，则照常行动，弃掉【封魔阵】；如果判定结果不是红桃，则该回合跳过出牌阶段（照常摸牌和弃牌），弃掉【封魔阵】。\n'
        u'|B|R>> |r仅当需要开始进行【封魔阵】的判定时,才能使用【好人卡】抵消之(抵消后弃掉【封魔阵】)。'
    )

    def is_action_valid(g, cl, target_list):
        if len(target_list) != 1:
            return (False, u'请选择封魔阵的目标')
        t = target_list[0]
        if g.me is t:
            return (False, u'你不能跟自己过不去啊！')

        return (True, u'画个圈圈诅咒你！')

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
        u'|B|R>> |r仅当需要开始进行【冻青蛙】的判定时,才能使用【好人卡】抵消之(抵消后弃掉【冻青蛙】)。'
    )

    def is_action_valid(g, cl, target_list):
        if len(target_list) != 1:
            return (False, u'请选择冻青蛙的目标')
        t = target_list[0]
        if g.me is t:
            return (False, u'你不能跟自己过不去啊！')

        return (True, u'伸手党什么的，冻住就好了！')

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
        u'出牌阶段使用，从牌堆摸两张牌。'
    )
    def is_action_valid(g, cl, target_list):
        t = target_list[0]
        return (True, u'看看能找到什么好东西~')

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
        u'|B|R>> |r仅当需要开始进行【罪袋】的判定时,才能使用【好人卡】抵消之,但抵消后不弃掉【罪袋】,而是将之传递给下家。'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'别来找我！')

class Sinsack:
    def effect_string(act):
        tgt = act.target
        if act.succeeded:
            return u'罪袋终于找到了机会，将|G【%s】|r推倒了…' % tgt.ui_meta.char_name

def equip_iav(g, cl, target_list):
    t = target_list[0]
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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class OpticalCloakHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【光学迷彩】吗？'

class OpticalCloak:
    def effect_string_before(act):
        return u'|G【%s】|r祭起了|G光学迷彩|r…' % (
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        if act.succeeded:
            return u'效果拔群！'
        else:
            return u'但是被看穿了…'


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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class YukariDimensionCard:
    # action_stage meta
    image = gres.card_yukaridimension
    name = u'隙间'

    description = (
        u'|R隙间|r\n\n'
        u'出牌阶段对距离为1的一名玩家使用，随机抽取并获得对方一张手牌，或选择并获得一张对方面前的牌(包括装备、明牌区内的牌和判定区的延时类符卡)。'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择目标')

        target= target_list[0]
        if not (target.cards or target.showncards or target.equips or target.fatetell):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'请把胖次给我！')

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
        u'出牌阶段对(除自己外)任意一名玩家使用，由目标角色先开始，你和他（她）轮流打出一张【弹幕】，【弹幕战】对首先不出【弹幕】的一方造成1点伤害；另一方成为此伤害的来源。'
    )
    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择弹幕战的目标')

        target= target_list[0]
        return (True, u'来，战个痛快！')

class MapCannonCard:
    image = gres.card_mapcannon
    name = u'地图炮'
    description = (
        u'|R地图炮|r\n\n'
        u'按行动顺序结算，除非目标角色打出一张【擦弹】，否则该角色受到【地图炮】对其造成的1点伤害。'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'一个都不能跑！')

class SinsackCarnivalCard:
    image = gres.card_sinsackcarnival
    name = u'罪袋狂欢'
    description = (
        u'|R罪袋狂欢|r\n\n'
        u'出牌阶段使用,(除自己外)所有玩家各需出一张【弹幕】，没有【弹幕】（或不出）的玩家受到一点伤害。'
    )
    def is_action_valid(g, cl, target_list):
        return (True, u'罪袋们来送水啦！')

class HakuroukenCard:
    # action_stage meta
    name = u'白楼剑'
    image = gres.card_hakurouken
    image_small = gres.card_hakurouken_small
    description = (
        u'|R白楼剑|r\n\n'
        u'攻击范围2，每当你使用【弹幕】攻击一名角色时，无视该角色的防具。'
    )
    is_action_valid = equip_iav

class HakuroukenSkill:
    # Skill
    name = u'白楼剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Hakurouken:
    def effect_string_apply(act):
        a = act.action
        src, tgt = a.source, a.target
        return u'|G【%s】|r祭起了|G白楼剑|r，直斩|G【%s】|r的魂魄！' % (
            src.ui_meta.char_name,
            tgt.ui_meta.char_name,
        )

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class UmbrellaCard:
    # action_stage meta
    name = u'阳伞'
    image = gres.card_umbrella
    image_small = gres.card_umbrella_small
    description = (
        u'|R阳伞|r\n\n'
        u'装备后不受【地图炮】和【罪袋狂欢】的影响。'
    )

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
    description = (
        u'|R楼观剑|r\n\n'
        u'攻击范围3，当你使用的【弹幕】被抵消时，你可以立即对相同的目标再使用一张【弹幕】。'
    )
    is_action_valid = equip_iav

class RoukankenSkill:
    # Skill
    name = u'楼观剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class RoukankenHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'再来一刀！')
        else:
            return (False, u'请使用【弹幕】发动楼观剑……')

class RoukankenLaunchAttack:
    def effect_string_before(act):
        return (
            u'虽然上一刀落空了，但是|G楼观剑|r的气势并未褪去。' +
            u'|G【%s】|r调整了姿势，再次向|G【%s】|r出刀！'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,

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

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[-1]
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
        # for LaunchCard.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r发动了|G冈格尼尔|r之枪，将两张牌当作|G弹幕|r对|G【%s】|r使用。' % (
            source.ui_meta.char_name,
            target.ui_meta.char_name,
        )
        return s

class LaevateinCard:
    # action_stage meta
    name = u'莱瓦汀'
    image = gres.card_laevatein
    image_small = gres.card_laevatein_small
    description = (
        u'|R莱瓦汀|r\n\n'
        u'攻击范围4，当你使用的【弹幕】是你的最后一张手牌时，你可以为这张【弹幕】指定至多三名目标，然后依次结算之。'
    )

    is_action_valid = equip_iav

class LaevateinSkill:
    # Skill
    name = u'莱瓦汀'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[-1]
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
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        tl = BatchList(act.target_list)

        return u'|G【%s】|r不顾危险发动了|G莱瓦汀|r，火焰立刻扑向了对|G【%s】|r！' % (
            source.ui_meta.char_name,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

class TridentCard:
    # action_stage meta
    name = u"三叉戟"
    image = gres.card_trident
    image_small = gres.card_trident_small
    description = (
        u'|R三叉戟|r\n\n'
        u'攻击范围5，你使用【弹幕】对一名角色造成伤害时，你可以弃掉对方装备区里的一个UFO。'
    )


    is_action_valid = equip_iav

class TridentSkill:
    # Skill
    name = u"三叉戟"

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

class FeastCard:
    # action_stage meta
    image = gres.card_feast
    name = u'宴会'
    description = (
        u'|R宴会|r\n\n'
        u'对所有玩家生效，每一个体力不满的玩家回复一点体力，满体力玩家获得|B喝醉|r状态。'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'开宴啦~~')

class HarvestCard:
    # action_stage meta
    image = gres.card_harvest
    name = u'五谷丰登'
    description = (
        u'|R五谷丰登|r\n\n'
        u'你从牌堆顶亮出等同于现存角色数量的牌，然后所有角色按行动顺序结算，选择并获得这些牌中的一张。'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'麻薯会有的，节操是没有的！')

class HarvestEffect:
    def effect_string(act):
        if not act.succeeded: return None
        tgt = act.target
        c = act.card
        return u'|G【%s】|r获得了|G%s|r' % (
            tgt.ui_meta.char_name,
            c.ui_meta.name,
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
    description = (
        u'|R伊吹瓢|r\n\n'
        u'当装备在进攻马位置。在装备、失去装备及回合结束时获得|B喝醉|r状态'
    )

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
    description = (
        u'|R蓬莱玉枝|r\n\n'
        u'攻击范围1，当使用【弹幕】时可以选择发动。发动后【弹幕】带有符卡性质，可以被【好人卡】抵消，不可以使用【擦弹】躲过。\n'
        u'|R>> |r计算在出【弹幕】的次数内。\n'
        u'|R>> |r蓬莱玉枝造成的伤害为固定的1点'
    )

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class SaigyouBranchHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【西行妖枝条】吗？'

class SaigyouBranch:
    def effect_string_before(act):
        return (
            u'|G西行妖|r的枝条受到了|G【%s】|r春度的滋养，' +
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

class FlirtingSwordCard:
    # action_stage meta
    name = u'调教剑'
    image = gres.card_flirtingsword
    image_small = gres.card_flirtingsword_small
    description = (
        u'|R调教剑|r\n\n'
        u'攻击范围2，你使用【弹幕】，指定了一名角色为目标后，你可以令对方选择一项：自己弃一张手牌或让你从牌堆摸一张牌。'
    )
    is_action_valid = equip_iav

class FlirtingSwordSkill:
    # Skill
    name = u'调教剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class FlirtingSword:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'才……才不给你机会呢！')
        else:
            return (False, u'请弃掉一张牌（否则对方摸一张牌）')

    def effect_string_before(act):
        return (
            u'|G【%s】|r拿起了|G调教剑|r，对着|G【%s】|r做起了啪啪啪的事！'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        if act.peer_action == 'drop':
            return (
                u'但是|G【%s】|r不太情愿，拿起一张牌甩在了|G【%s】|r的脸上！'
            ) % (
                act.target.ui_meta.char_name,
                act.source.ui_meta.char_name,
            )
        else:
            return (
                u'|G【%s】|r被（哗）后，|G【%s】|r居然摆着人生赢家的姿态摸了一张牌！'
            ) % (
                act.target.ui_meta.char_name,
                act.source.ui_meta.char_name,
            )

class FlirtingSwordHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【调教剑】吗？'

class CameraCard:
    # action_stage meta
    name = u'相机'
    image = gres.card_camera
    description = (
        u'|R相机|r\n\n'
        u'将除了你之外的任意一名玩家的2张手牌置入明牌区'
    )

    def is_action_valid(g, cl, tl):
        if not tl:
            return (False, u'请选择目标')
        t = tl[0]

        if not t.cards:
            return (True, u'这货已经没有隐藏的手牌了')

        return (True, u'摄影的境界，你们这些玩器材的永远都不会懂！')

class AyaRoundfanCard:
    # action_stage meta
    name = u'团扇'
    image = gres.card_ayaroundfan
    image_small = gres.card_ayaroundfan_small
    description = (
        u'|R团扇|r\n\n'
        u'攻击距离3，当你使用【弹幕】命中时，可以弃一张手牌，卸掉目标的一件装备。'
    )
    is_action_valid = equip_iav

class AyaRoundfanSkill:
    # Skill
    name = u'团扇'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

class ScarletRhapsodySwordCard:
    # action_stage meta
    name = u'绯想之剑'
    image = gres.card_scarletrhapsodysword
    image_small = gres.card_scarletrhapsodysword_small
    description = (
        u'|R绯想之剑|r\n\n'
        u'攻击距离3，目标角色使用【擦弹】抵消你使用【弹幕】的效果时，你可以弃两张牌（可以是手牌也可以是自己的其它装备牌），强制命中对方，对方无法闪避（则【弹幕】依然造成伤害）。'
    )
    is_action_valid = equip_iav

class ScarletRhapsodySwordSkill:
    # Skill
    name = u'绯想之剑'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class ScarletRhapsodySwordAttack:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'闪过头了！')
        else:
            return (False, u'请弃掉两张牌发动绯想之剑（否则不发动）')

class ScarletRhapsodySword:
    def effect_string_before(act):
        sn, tn = act.source.ui_meta.char_name, act.target.ui_meta.char_name
        return (
            u'但是弱点早已被|G绯想之剑|r看穿，在|G【%s】|r还未' +
            u'停稳脚步时，|G【%s】|r给了她精准的一击！'
        ) % (
            tn, sn
        )

class DeathSickleCard:
    # action_stage meta
    name = u'死神之镰'
    image = gres.card_deathsickle
    image_small = gres.card_deathsickle_small
    description = (
        u'|R死神之镰|r\n\n'
        u'攻击范围2，锁定技，当你使用的【弹幕】时，若指定的目标没有手牌，结算时伤害+1。'
    )
    is_action_valid = equip_iav

class DeathSickleSkill:
    # Skill
    name = u'死神之镰'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class YinYangOrbHandler:
    # choose_option
    choose_option_buttons = ((u'替换', True), (u'不替换', False))
    choose_option_prompt = u'你要使用【阴阳玉】替换当前的判定牌吗？'

class YinYangOrb:
    def effect_string(act):
        return (
            u'|G【%s】|r用|G阴阳玉|r代替了她的判定牌'
        ) % (
            act.target.ui_meta.char_name,
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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

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
                if me.tags.get('attack_num', 0):
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

class DollControlCard:
    # action_stage meta
    name = u'人形操控'
    image = gres.card_dollcontrol
    description = (
        u'|R人形操控|r\n\n'
        u'对装备有武器的玩家使用，令其使用一张【弹幕】攻击另一名指定玩家，否则将武器交给自己。'
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
            from .. import actions, cards
            c = cards.AttackCard()
            lc = actions.LaunchCard(tl[0], [tl[1]], c)
            if not lc.can_fire():
                return (False, u'被控者无法向目标出【弹幕】！')
            return (True, u'乖，听话！')

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
        u'指定1-2名有手牌或装备的玩家，被指定玩家必须选择一张手牌或装备牌置入你的明牌区。'
    )

    def is_action_valid(g, cl, tl):
        n = len(tl)
        if not n:
            return (False, u'请选择1-2名玩家')

        #if g.me in tl:
        #    return (False, u'你不能选择自己作为目标')

        for t in tl:
            if not (t.cards or t.showncards or t.equips):
                return (False, u'目标没有可以给你的牌')

        return (True, u'纳奉！纳奉！')

class DonationBoxEffect:
    # choose card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'这是抢劫啊！')
        else:
            return (False, u'请选择一张牌（否则会随机选择一张）')


class LotteryCard:
    # action_stage meta
    name = u'御神签'
    image = gres.card_lottery
    description = (
        u'|R御神签|r\n\n'
        u'符卡，你可以选择1名玩家作为目标（或不选）。当你使用此符卡时，你摸一张牌。若选择了目标，则目标翻开牌堆顶的一张牌：\n'
        u'|B|R>> |r红桃：目标可以将场上的任意一张牌收入手牌\n'
        u'|B|R>> |r方片：目标可以弃置至多2张手牌，并且摸相同数量的牌\n'
        u'|B|R>> |r草花：目标须弃置一张牌\n'
        u'|B|R>> |r黑桃：目标流失1点体力'
    )

    def is_action_valid(g, cl, tl):
        n = len(tl)
        if n == 0:
            return (True, u'请选择目标（或者不选）')

        return (True, u'运气也是实力的一部分！')


class LotteryHeart:
    # choose_players
    def target(pl):
        if not pl:
            return (True, u'御神签效果：请选择1玩家，抽取一张牌(或不选)')

        return (True, u'收集信仰！')

    def effect_string_apply(act):
        return u'大吉！'


class LotteryDiamond:
    # choose card meta
    def choose_card_text(g, act, cards):
        return (True, u'御神签效果：请选择至多2张手牌换走（或不选）')

    def effect_string_apply(act):
        return u'小吉！'


class LotteryClub:
    # choose card meta
    def choose_card_text(g, act, cards):
        return (True, u'御神签效果：请选择1张牌弃置')

    def effect_string_apply(act):
        return u'小凶！'


class LotterySpade:
    def effect_string_apply(act):
        return u'大凶！'


# -----END CARDS UI META-----

# -----BEGIN CHARACTERS UI META-----
__metaclass__ = gen_metafunc(characters.parsee)

class Parsee:
    # Character
    char_name = u'水桥帕露西'
    port_image = gres.parsee_port
    description = (
        u'|DB地壳下的嫉妒心 水桥帕露西 体力：4|r\n\n'
        u'|G嫉妒|r：出牌阶段，你可以将你的黑色的手牌或装备牌牌当【城管执法】使用。'
    )

class Envy:
    # Skill
    name = u'嫉妒'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.parsee.Envy)
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.suit not in (cards.Card.SPADE, cards.Card.CLUB):
                return (False, u'请选择一张黑色的牌！')
            return cards.DemolitionCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r发动了嫉妒技能，将|G%s|r当作|G%s|r对|G【%s】|r使用。' % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            target.ui_meta.char_name,
        )
        return s

# ----------
__metaclass__ = gen_metafunc(characters.youmu)

class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = gres.youmu_port
    description = (
        u'|DB半分虚幻的庭师 魂魄妖梦 体力：4|r\n\n'
        u'|G迷津慈航斩|r：|B锁定技|r，你使用【弹幕】时，目标角色需连续使用两张【擦弹】才能抵消；与你进行【弹幕战】的角色每次需连续打出两张【弹幕】。\n\n'
        u'|G二刀流|r：你可以同时装备两把武器。同时装备时，攻击距离加成按其中较低者计算，武器技能同时有效。\n'
        u'|B|R>> |r成为【人形操控】目标并且不出【弹幕】的话，两把武器会被一起拿走\n\n'
        u'|G现世妄执|r：|B觉醒技|r，同时装备了楼观剑与白楼剑获得此技能（卸掉/更换装备不会失去）。一回合内你可以使用两张【弹幕】。'
    )

class Mijincihangzhan:
    # Skill
    name = u'迷津慈航斩'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class MijincihangzhanAttack:
    def effect_string_apply(act):
        src = act.source
        tgt = act.target
        return u'|G【%s】|r在弹幕中注入了妖力，弹幕形成了一个巨大的光刃，怕是不能轻易地闪开的！' % (
            src.ui_meta.char_name,
        )

class Nitoryuu:
    # Skill
    name = u'二刀流'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Xianshiwangzhi:
    # Skill
    name = u'现世妄执'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')


# ----------
__metaclass__ = gen_metafunc(characters.koakuma)

class Koakuma:
    # Character
    char_name = u'小恶魔'
    port_image = gres.koakuma_port
    description = (
        u'|DB图书管理员 小恶魔 体力：4|r\n\n'
        u'|G寻找|r：出牌阶段，你可以弃掉任意数量的牌，然后摸取等量的牌。每回合里，你最多可以使用一次寻找。'
    )

class Find:
    # Skill
    name = u'寻找'

    def clickable(game):
        me = game.me
        if me.tags.get('find_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.koakuma.Find)
        if not len(skill.associated_cards):
            return (False, u'请选择需要换掉的牌！')

        if not [g.me] == target_list:
            return (False, 'BUG!!')

        return (True, u'换掉这些牌')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r发动了寻找技能，换掉了%d张牌。' % (
            source.ui_meta.char_name,
            len(card.associated_cards),
        )
        return s

# ----------
__metaclass__ = gen_metafunc(characters.marisa)

class Marisa:
    # Character
    char_name = u'雾雨魔理沙'
    port_image = gres.marisa_port
    description = (
        u'|DB绝非普通的强盗少女 雾雨魔理沙 体力：4|r\n\n'
        u'|G借走|r：摸牌阶段，你可以放弃摸牌，然后从至多两名角色的手牌里各抽取一张牌，置入你的明牌区。\n\n'
        u'|G极限火花|r：你可以使用两张【擦弹】作为一张无距离限制的【弹幕】使用或打出。'
    )

class MasterSpark:
    # Skill
    name = u'极限火花'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if act.target is not me: return False
        if not (me.cards or me.showncards): return False

        if isinstance(act, actions.ActionStage):
            return True

        if isinstance(act, (cards.UseAttack, cards.BaseUseGraze, cards.DollControl)):
            return True

        return False


    def is_complete(g, cl):
        cl = cl[0].associated_cards
        if not (cl and len(cl) == 2 and all(c.is_card(cards.GrazeCard) for c in cl)):
            return (False, u'请选择两张【擦弹】')

        return (True, u'nyan')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        rst, reason = is_complete(g, cl)
        if not rst:
            return rst, reason

        if len(target_list) != 1:
            return (False, u'请选择1名玩家')

        return (True, u'MASTER SPARK！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r向|G【%s】|r发动了|G极限火花|r……打的真远！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

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

class BorrowAction:
    def effect_string(act):
        return u'大盗|G【%s】|r又跑出来“|G借走|r”了|G【%s】|r的牌。' % (
            act.source.ui_meta.char_name,
            u'】|r和|G【'.join(BatchList(act.target_list).ui_meta.char_name),
        )

# ----------
__metaclass__ = gen_metafunc(characters.daiyousei)

class Daiyousei:
    # Character
    char_name = u'大妖精'
    port_image = gres.daiyousei_port
    description = (
        u'|DB全身萌点的保姆 大妖精 体力：3|r\n\n'
        u'|G支援|r：出牌阶段，你可以将任意数量的除了判定区外的牌以任意分配方式交给其他角色，若你于此阶段中给出的牌张数达到或超过3张时，你回复1点体力。\n\n'
        u'|G卖萌|r：摸牌阶段，你可以摸 2+当前损失的体力数 的牌。'
    )

class SupportSkill:
    # Skill
    name = u'支援'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        me = g.me
        allcards = list(me.cards) + list(me.showncards) + list(me.equips)
        if any(
            c not in allcards
            for c in cl
        ): return (False, u'你只能选择手牌与装备牌！')
        if len(target_list) != 1: return (False, u'请选择1名玩家')
        return (True, u'加油！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r发动了|G支援|r技能，将%d张牌交给了|G【%s】|r' % (
            act.source.ui_meta.char_name,
            len(act.card.associated_cards),
            act.target.ui_meta.char_name,
        )

class Moe:
    # Skill
    name = u'卖萌'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class MoeDrawCard:
    def effect_string(act):
        return u'|G【%s】|r用手扯开脸颊，向大家做了一个夸张的笑脸，摸了%d张牌跑开了' % (
            act.target.ui_meta.char_name,
            act.amount,
        )

# ----------
__metaclass__ = gen_metafunc(characters.flandre)

class Flandre:
    # Character
    char_name = u'芙兰朵露'
    port_image = gres.flandre_port
    description = (
        u'|DB玩坏你哦 芙兰朵露 体力：4|r\n\n'
        u'|G狂咲|r：在你的摸牌阶段，如果你选择只摸一张牌，那么在你的出牌阶段你可以出任意张【弹幕】，并且【弹幕】和【弹幕战】的伤害为2点，但是对同一目标只能使用一张【弹幕】。'
    )

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

class CriticalStrikeAction:
    def effect_string(act):
        return u'|G【%s】|r突然呵呵一笑，进入了黑化状态！' % (
            act.target.ui_meta.char_name,
        )

# ----------
__metaclass__ = gen_metafunc(characters.alice)

class Alice:
    # Character
    char_name = u'爱丽丝'
    port_image = gres.alice_port
    description = (
        u'|DB七色的人偶使 爱丽丝 体力：4|r\n\n'
        u'|G人形操演|r：出牌阶段，你可以使用任意数量的【弹幕】。\n\n'
        u'|G玩偶十字军|r：出牌阶段，你可以将你的饰品作为【人形操控】使用。'
    )

class DollManipulation:
    # Skill
    name = u'人形操演'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class DollCrusader:
    # Skill
    name = u'玩偶十字军'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and \
            act.target is me and \
            (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        while True:
            if len(cl) != 1: break
            c = cl[0]
            cat = getattr(c, 'equipment_category', None)
            if cat != 'accessories': break
            return cards.DollControlCard.ui_meta.is_action_valid(g, [skill], target_list)

        return (False, u'请选择一张饰品！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r突然向|G【%s】|r射出魔法丝线，将她当作玩偶一样玩弄了起来！' % (
            source.ui_meta.char_name,
            target.ui_meta.char_name,
        )
        return s

# ----------
__metaclass__ = gen_metafunc(characters.nazrin)

class Nazrin:
    # Character
    char_name = u'娜滋琳'
    port_image = gres.nazrin_port
    description = (
        u'|DB探宝的小小大将 娜滋琳 体力：3|r\n\n'
        u'|G轻敏|r：你可以将你的黑色手牌当作【擦弹】使用或打出。\n\n'
        u'|G探宝|r：回合开始阶段，你可以进行判定：若为黑色，立即获得此牌，并且可以继续发动探宝；直到出现红色牌为止。'
    )

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
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, cards.BaseUseGraze) and (me.cards or me.showncards):
            return True

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.resides_in not in (g.me.cards, g.me.showncards):
                return (False, u'请选择手牌！')
            if c.suit not in (cards.Card.SPADE, cards.Card.CLUB):
                return (False, u'请选择一张黑色的牌！')
            return (True, u'这种三脚猫的弹幕，想要打中我是不可能的啦~')

class TreasureHunt:
    def effect_string(act):
        if act.succeeded:
            return u'|G【%s】|r找到了|G%s|r' % (
                act.target.ui_meta.char_name,
                act.card.ui_meta.name,
            )
        else:
            return u'|G【%s】|r什么也没有找到…' % (
                act.target.ui_meta.char_name,
            )

# ----------
__metaclass__ = gen_metafunc(characters.yugi)

class Yugi:
    # Character
    char_name = u'星熊勇仪'
    port_image = gres.yugi_port
    description = (
        u'|DB人所谈论的怪力乱神 星熊勇仪 体力：4|r\n\n'
        #u'|G强袭|r：你可以自损1点体力，或者使用一张武器牌/【酒】，对任意一名在你的攻击范围内的玩家造成一点伤害。\n\n'
        u'|G强袭|r：你与其他玩家结算距离时始终-1\n\n'
        u'|G怪力|r：你对别的角色出【弹幕】时可以选择做一次判定：若判定牌为红色花色，则此【弹幕】不可回避，直接命中；若判定牌为黑色花色，则此【弹幕】可回避，但如果对方没有出【擦弹】，则命中后可以选择弃掉对方一张牌。'
    )

class AssaultSkill:
    # Skill
    name = u'强袭'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

'''
    def clickable(game):
        me = game.me
        if me.tags.get('yugi_assault', 0) >= me.tags.get('turn_count', 0):
            return False
        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        return isinstance(act, actions.ActionStage)

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择强袭的目标，以及一张武器牌或者【酒】（不选自己会受到1点伤害）')

        if g.me is target_list[0]:
            return (False, u'不可以对自己发动')
        else:
            return (True, u'[不知道该说什么，先这样吧]')

    def effect_string(act):
        return u'|G【%s】|r向|G【%s】|r发动了|G强袭|r技能' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )
'''

class FreakingPowerSkill:
    # Skill
    name = u'怪力'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class FreakingPower:
    def effect_string_before(act):
        return u'|G【%s】|r稍微认真了一下，弹幕以惊人的速度冲向|G【%s】|r' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class YugiHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【怪力】吗？'

# ----------
__metaclass__ = gen_metafunc(characters.patchouli)

class Library:
    # Skill
    name = u'图书'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class LibraryDrawCards:
    def effect_string(act):
        return u'|G【%s】|r发动了|G图书|r技能，摸1张牌。' % (
            act.source.ui_meta.char_name,
        )

class Knowledge:
    # Skill
    name = u'博学'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class KnowledgeAction:
    def effect_string(act):
        return u'|G【%s】|r一眼就看穿了这张符卡，直接挡下。' % (
            act.source.ui_meta.char_name,
        )

class Patchouli:
    # Character
    char_name = u'帕秋莉'
    port_image = gres.patchouli_port
    description = (
        u'|DB不动的大图书馆 帕秋莉 体力：3|r\n\n'
        u'|G图书|r：|B锁定技|r，每当你使用了一张非延时符卡时，你摸一张牌。\n\n'
        u'|G博学|r：|B锁定技|r，黑桃色符卡对你无效。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.tewi)

class Luck:
    # Skill
    name = u'幸运'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class LuckDrawCards:
    def effect_string(act):
        return u'|G【%s】|r觉得手上没有牌就输了，于是又摸了2张牌。' % (
            act.source.ui_meta.char_name,
        )

class Tewi:
    # Character
    char_name = u'因幡帝'
    port_image = gres.tewi_port
    description = (
        u'|DB幸运的腹黑兔子 因幡帝 体力：4|r\n\n'
        u'|G幸运|r：|B锁定技|r，当你的手牌数为0时，立即摸2张牌。'
    )

'''
# ----------
__metaclass__ = gen_metafunc(characters.reimu_old)

class SealingArraySkill:
    # Skill
    name = u'封魔阵'
    image = gres.card_sealarray
    tag_anim = lambda c: gres.tag_sealarray
    description = (
        u'|G【博丽灵梦】|r的技能产生的封魔阵'
    )

    def clickable(game):
        me = game.me

        if me.tags.get('reimusa_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[-1]
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
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        return (
            u'|G【%s】|r发动了|G封魔阵|r技能，用|G%s|r' +
            u'在|G【%s】|r的脚下画了一个大圈圈！'
        ) % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.char_name,
        )

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
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, tl):
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        if len(cl) != 1: return (False, u'只能选择一张手牌')

        from ..cards import CardList
        if not cl[0].resides_in.type in ('handcard', 'showncard'):
            return (False, u'只能选择手牌！')

        if len(tl) != 1 or not tl[0].has_skill(characters.reimu_old.TributeTarget):
            return (False, u'请选择一只灵梦')

        return (True, u'塞钱……会发生什么呢？')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r向|G【%s】|r的塞钱箱里放了一张牌… 会发生什么呢？'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class Reimu:
    # Character
    char_name = u'博丽灵梦'
    port_image = gres.reimu_port
    description = (
        u'|DB乐园奇妙的无节操巫女 博丽灵梦 体力：3|r\n\n'
        u'|G封魔阵|r：出牌阶段，你可以用一张方块牌当做【封魔阵】使用，一回合一次。\n\n'
        #u'|G飞行|r：锁定技，其他玩家对你结算距离时始终+1\n\n'
        u'|G纳奉|r：任何人都可以在自己的出牌阶段给你一张手牌。'
    )
'''

# ----------
__metaclass__ = gen_metafunc(characters.cirno)

class PerfectFreeze:
    # Skill
    name = u'完美冻结'

    @property
    def image(c):
        return c.associated_cards[0].ui_meta.image

    tag_anim = lambda c: gres.tag_frozenfrog
    description = (
        u'|G【琪露诺】|r的技能产生的【冻青蛙】'
    )

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and act.target is me and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.suit in (cards.Card.SPADE, cards.Card.CLUB):
                act = c.associated_action
                if act and issubclass(act, (cards.BasicAction, cards.WearEquipmentAction)):
                    return (True, u'PERFECT FREEZE~')

            return (False, u'请选择一张黑色的基本牌或装备牌！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        return (
            u'|G【%s】|r发动了|G完美冻结|r技能，用|G%s|r' +
            u'把|G【%s】|r装进了大冰块里！'
        ) % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.char_name,
        )

class Cirno:
    # Character
    char_name = u'琪露诺'
    port_image = gres.cirno_port
    description = (
        u'|DB跟青蛙过不去的笨蛋 琪露诺 体力：4|r\n\n'
        u'|G完美冻结|r：出牌阶段，可以将你的任意一张黑色的基本牌或装备牌当【冻青蛙】使用；你可以对与你距离2以内的角色使用【冻青蛙】。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.reimu)

class Flight:
    # Skill
    name = u'飞行'
    no_display = False

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class SpiritualAttack:
    name = u'灵击'

    def clickable(game):
        return True # FIXME: !!!!!!

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        assert skill.is_card(characters.reimu.SpiritualAttack)
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择1张手牌！')

        c = acards[0]

        if c.resides_in not in (me.cards, me.showncards):
            return (False, u'只能使用手牌发动！')
        elif not c.color == cards.Card.RED:
            return (False, u'请选择红色手牌！')

        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动使用灵击')

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
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, tl):
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        if len(cl) != 1: return (False, u'只能选择一张手牌')

        from ..cards import CardList
        if not cl[0].resides_in.type in ('handcard', 'showncard'):
            return (False, u'只能选择手牌！')

        if len(tl) != 1 or not tl[0].has_skill(characters.reimu.TributeTarget):
            return (False, u'请选择一只灵梦')

        return (True, u'塞钱……会发生什么呢？')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r向|G【%s】|r的塞钱箱里放了一张牌… 会发生什么呢？'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class Reimu:
    # Character
    char_name = u'博丽灵梦'
    port_image = gres.reimu_port
    description = (
        u'|DB节操满地跑的城管 博丽灵梦 体力：3|r\n\n'
        u'|G灵击|r：你可以将你的任意一张红色手牌当【好人卡】使用。\n\n'
        u'|G飞行|r：锁定技，当你没有装备任何UFO时，其他玩家对你结算距离时始终+1\n\n'
        u'|G纳奉|r：任何人都可以在自己的出牌阶段给你一张手牌。'
    )


# ----------
__metaclass__ = gen_metafunc(characters.kogasa)

class Jolly:
    # Skill
    name = u'愉快'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class JollyDrawCard:
    def effect_string(act):
        return u'|G【%s】|r高兴地让|G【%s】|r摸了%d张牌~' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.amount,
        )

class JollyHandler:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家，该玩家摸一张牌')

        return (True, u'(～￣▽￣)～')

class SurpriseSkill:
    # Skill
    name = u'惊吓'

    def clickable(game):
        me = game.me

        if me.tags.get('surprise_tag', 0) >= me.tags.get('turn_count', 0):
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards):
            return True

        return False

    def is_action_valid(g, cl, tl):
        if len(tl) != 1:
            return (False, u'请选择惊吓对象…')

        if len(cl[0].associated_cards):
            return (False, u'请不要选择牌！')

        #return (True, u'(´・ω・`)')
        return (True, u'\ ( °▽ °) /')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r突然出现在|G【%s】|r面前，伞上'
            u'的大舌头直接糊在了|G【%s】|r的脸上！'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class Surprise:
    # choose_option
    choose_option_buttons = (
        (u'黑桃', cards.Card.SPADE),
        (u'红桃', cards.Card.HEART),
        (u'草花', cards.Card.CLUB),
        (u'方片', cards.Card.DIAMOND),
    )
    choose_option_prompt = u'请选择一个花色…'

    def effect_string(act):
        if act.succeeded:
            return u'效果拔群！'
        else:
            return u'似乎没有什么效果'

class Kogasa:
    # Character
    char_name = u'多多良小伞'
    port_image = gres.kogasa_port
    description = (
        u'|DB愉快的遗忘之伞 多多良小伞 体力：3|r\n\n'
        u'|G惊吓|r：出牌阶段，你可以指定另一名角色选择一种花色，抽取你的一张手牌并亮出，若此牌与所选花色不吻合，则你对该角色造成1点伤害。然后不论结果，该角色都获得此牌，你摸一张牌。每回合限用一次。\n\n'
        u'|G愉快|r：摸牌阶段摸牌后，你可以指定一人摸1张牌。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.eirin)

class FirstAid:
    # Skill
    name = u'急救'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, cards.UseHeal):
            return True

        return False

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        acards = skill.associated_cards
        C = cards.Card
        if len(acards) != 1 or acards[0].suit not in (C.DIAMOND, C.HEART):
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
            act = game.action_stack[-1]
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
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r用一张|G%s|r做药引做了一贴膏药，'
            u'细心地贴在了|G【%s】|r的伤口上。'
        ) % (
            act.source.ui_meta.char_name,
            act.card.associated_cards[0].ui_meta.name,
            act.target.ui_meta.char_name,
        )

class Eirin:
    # Character
    char_name = u'八意永琳'
    port_image = gres.eirin_port
    description = (
        u'|DB街中的药贩 八意永琳 体力：3|r\n\n'
        u'|G医者|r：出牌阶段，你可以主动弃掉一张手牌，令任一目标角色回复1点体力。每回合限一次。\n\n'
        u'|G急救|r：当任意人进入濒死状态时，你可以将你的红色手牌或装备牌当做【麻薯】使用。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.shikieiki)

class Trial:
    # Skill
    name = u'审判'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class TrialAction:
    def effect_string(act):
        return u'幻想乡各地巫女妖怪纷纷表示坚决拥护|G【%s】|r将|G【%s】|r的判定结果修改为%s的有关决定！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            card_suitnum(act.card)
        )

class Majesty:
    # Skill
    name = u'威严'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class MajestyAction:
    def effect_string(act):
        return u'|G【%s】|r脸上挂满黑线，收走了|G【%s】|r的一张牌作为罚款' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class TrialHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【审判】吗？'

    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'有罪！')
        else:
            return (False, u'请选择一张牌代替当前的判定牌')

class MajestyHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【威严】吗？'

class Shikieiki:
    # Character
    char_name = u'四季映姬'
    port_image = gres.shikieiki_port
    description = (
        u'|DB乐园的最高裁判长 四季映姬 体力：3|r\n\n'
        u'|G审判|r：在任意角色的判定牌生效前，你可以打出一张牌代替之。\n\n'
        u'|G威严|r：可以立即从对你造成伤害的来源处获得一张牌。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.tenshi)

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

class MasochistAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'给你牌~')
        else:
            return (False, u'请选择你要给出的牌（否则给自己）')

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'给你牌~')

    def effect_string_before(act):
        return u'不过|G【%s】|r好像很享受的样子…' % (
            act.target.ui_meta.char_name,
        )

class Hermit:
    # Skill
    name = u'天人'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Tenshi:
    # Character
    char_name = u'比那名居天子'
    port_image = gres.tenshi_port
    description = (
        u'|DB有顶天的大M子 比那名居天子 体力：3|r\n\n'
        u'|G抖Ｍ|r：每当你受到X点伤害，你可以摸X*2张牌，然后将这些牌分配给任意的角色。\n\n'
        u'|G天人|r：在你的判定结束后，你获得该判定牌。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.yuuka)

class FlowerQueen:
    # Skill
    name = u'花王'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
            if isinstance(act, (cards.UseAttack, cards.BaseUseGraze, cards.DollControl)):
                return True
        except IndexError:
            pass
        return False

    def is_complete(g, cl):
        skill = cl[0]
        me = g.me
        acards = skill.associated_cards
        if len(acards) != 1 or acards[0].suit != cards.Card.CLUB:
            return (False, u'请选择1张草花色牌！')
        return (True, u'反正这条也看不到，偷个懒~~~')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return None # FIXME

class MagicCannon:
    # Skill
    name = u'魔炮'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class MagicCannonAttack:
    def effect_string_apply(act):
        return (
            u'|G【%s】|r已经做好了迎接弹幕的准备，谁知冲过来的竟是一束|G魔炮|r！'
        ) % (
            act.target.ui_meta.char_name,
        )

class PerfectKill:
    # Skill
    name = u'完杀'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class PerfectKillAction:
    def effect_string(act):
        return (
            u'在场的人无不被|G【%s】|r的气场镇住，竟连上前递|G麻薯|r的勇气都没有了！'
        ) % (
            act.source.ui_meta.char_name,
        )

class Yuuka:
    # Character
    char_name = u'风见幽香'
    port_image = gres.yuuka_port
    description = (
        u'|DB四季的鲜花之主 风见幽香 体力：3|r\n\n'
        u'|G花王|r：你的所有的梅花牌都可以当做【弹幕】和【擦弹】使用或打出。\n\n'
        u'|G魔炮|r：锁定技，你在使用红色的【弹幕】时伤害+1\n\n'
        u'|G完杀|r：锁定技，由你击杀的玩家只能由你的和被击杀玩家的【麻薯】救起。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.rumia)

class Darkness:
    # Skill
    name = u'黑暗'
    custom_ray = True

    def clickable(game):
        me = game.me
        try:
            tags = me.tags
            if tags['turn_count'] <= tags['darkness_tag']:
                return False
            act = game.action_stack[-1]
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
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r在黑暗中一通乱搅，结果|G【%s】|r和|G【%s】|r打了起来！' % (
            act.source.ui_meta.char_name,
            act.target_list[0].ui_meta.char_name,
            act.target_list[1].ui_meta.char_name,
        )


class DarknessAction:
    def ray(act):
        src = act.source
        tl = act.target_list
        return [(src, tl[1]), (tl[1], tl[0])]


class Cheating:
    # Skill
    name = u'作弊'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class CheatingDrawCards:
    def effect_string(act):
        return u'突然不知道是谁把太阳挡住了。等到大家回过神来，赫然发现牌堆里少了一张牌！'

class Rumia:
    # Character
    char_name = u'露米娅'
    port_image = gres.rumia_port
    description = (
        u'|DB宵暗的妖怪 露米娅 体力：3|r\n\n'
        u'|G黑暗|r：出牌阶段，你可以弃一张牌并选择两名角色。若如此做，视为由你选择的其中一名角色对另一名角色使用一张【弹幕战】。额外的，此【弹幕战】属于人物技能，不是符卡效果。\n\n'
        u'|G作弊|r：弃牌阶段后，你摸一张牌。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.rinnosuke)

class Netoru:
    # Skill
    name = u'寝取'

    def clickable(game):
        me = game.me
        try:
            if me.tags['netoru_tag'] >= me.tags['turn_count']:
                return False
            act = game.action_stack[-1]
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
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r一改平日的猥琐形象，竟然用花言巧语将|G【%s】|r骗去啪啪啪了！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class Psychopath:
    # Skill
    name = u'变态'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class PsychopathDrawCards:
    def effect_string(act):
        return (
            u'|G【%s】|r满脸猥琐地将装备脱掉，结果众人抄起了%d张牌糊在了他身上。'
        ) % (
            act.target.ui_meta.char_name,
            act.amount,
        )

class Rinnosuke:
    # Character
    char_name = u'森近霖之助'
    port_image = gres.rinnosuke_port
    description = (
        u'|DB变态出没注意 森近霖之助 体力：3|r\n\n'
        u'|G变态|r：当你失去一张装备区里的牌时，你可以立即摸两张牌。\n\n'
        u'|G寝取|r：出牌阶段，你可以弃两张手牌并指定一名除了你之外的受伤的角色：你和目标角色各回复1点体力。每回合限用一次。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.ran)

class Prophet:
    # Skill
    name = u'神算'

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

class ProphetHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神算】吗？'

class ProphetAction:
    def effect_string_before(act):
        return u'众人正准备接招呢，|G【%s】|r却掐着指头算了起来…' % (
            act.target.ui_meta.char_name,
        )

class ExtremeIntelligenceHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【极智】吗？'

class ExtremeIntelligenceAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'再来！')
        else:
            return (False, u'请选择1张牌弃置')

    def effect_string_before(act):
        return (
            u'|G【%s】|r刚松了一口气，却看见一张一模一样的符卡从|G【%s】|r的方向飞来！'
        ) % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
        )

class NakedFox:
    # Skill
    name = u'素裸'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class NakedFoxAction:
    def effect_string_before(act):
        if act.dmgamount <= 1:
            s = u'符卡飞到了|G【%s】|r毛茸茸的大尾巴里，然后……就没有然后了……'
        else:
            s = u'符卡飞到了|G【%s】|r毛茸茸的大尾巴里，恩……似乎还是有点疼……'

        return s % act.target.ui_meta.char_name

class Ran:
    # Character
    char_name = u'八云蓝'
    port_image = gres.ran_port
    description = (
        u'|DB天河一号的核心 八云蓝 体力：3|r\n\n'
        u'|G神算|r：在你的判定流程前，可以翻开等于场上存活人数（不超过5张）的牌，并以任意的顺序放回牌堆的上面或者下面。\n\n'
        u'|G极智|r：自己的回合外，当任何人发动除【好人卡】以外非延时符卡时，发动完成后，你可以选择弃一张牌，再次发动该符卡，目标不变，发动者算作你。一轮一次。\n\n'
        u'|G素裸|r：在你没有手牌时，你受到的符卡伤害-1'
    )

# ----------
__metaclass__ = gen_metafunc(characters.remilia)

class FateSpear:
    # Skill
    name = u'神枪'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class FateSpearAction:
    def effect_string(act):
        return u'|G【%s】|r举起右手，将|G弹幕|r汇聚成一把命运之矛，向|G【%s】|r掷去！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

class FateSpearHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神枪】吗？'

class VampireKiss:
    # Skill
    name = u'红魔之吻'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class VampireKissAction:
    def effect_string_before(act):
        return u'|G【%s】|r:“B型血，赞！”' % (
            act.source.ui_meta.char_name
        )

class Remilia:
    # Character
    char_name = u'蕾米莉亚'
    port_image = gres.remilia_port
    description = (
        u'|DB永远幼小的红月 蕾米莉亚 体力：4|r\n\n'
        u'|G神枪|r：出牌阶段，出现以下情况之一，你可以令你的【弹幕】不能被【擦弹】抵消：\n'
        u'|B|R>> |r目标角色的体力值 大于 你的体力值。\n'
        u'|B|R>> |r目标角色的手牌数 小于 你的手牌数。\n\n'
        u'|G红魔之吻|r：|B锁定技|r，对玩家使用红色【弹幕】命中时，回复1点体力值。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.minoriko)

class Foison:
    # Skill
    name = u'丰收'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class FoisonDrawCardStage:
    def effect_string(act):
        return u'大丰收！|G【%s】|r一下子收获了%d张牌！' % (
            act.source.ui_meta.char_name,
            act.amount,
        )

class AutumnFeast:
    # Skill
    name = u'秋祭'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if me.tags['autumnfeast_tag'] >= me.tags['turn_count']:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        from ..cards import Card
        if len(cl) != 2 or any(c.color != Card.RED for c in cl):
            return (False, u'请选择2张红色的牌！')
        return (True, u'发麻薯啦~')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        return (
            u'|G【%s】|r：麻薯年年有，今年特别多！'
        ) % (
            source.ui_meta.char_name,
        )

class AkiTribute:
    # Skill
    name = u'上贡'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Minoriko:
    # Character
    char_name = u'秋穰子'
    port_image = gres.minoriko_port
    description = (
        u'|DB没人气的丰收神 秋穰子 体力：3|r\n\n'
        u'|G丰收|r：|B锁定技|r，摸牌阶段摸牌后，若你的手牌数不足5张，你可以补至5张。\n\n'
        u'|G秋祭|r：你可以将两张红色的手牌或装备牌当作【五谷丰登】使用。一回合限一次。\n\n'
        u'|G上贡|r：|B锁定技|r，任何人使用【五谷丰登】时，你首先拿牌。在【五谷丰登】结算完毕后，若仍有牌没有被拿走，你将这些牌收入明牌区。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.meirin)

class RiverBehind:
    # Skill
    name = u'背水'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class Taichi:
    # Skill
    name = u'太极'

    def clickable(game):
        me = game.me
        try:
            act = game.action_stack[-1]
            if isinstance(act, (actions.ActionStage, cards.UseAttack, cards.DollControl, cards.BaseUseGraze)):
                return True
        except IndexError:
            pass
        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        from ..cards import Card, AttackCard, GrazeCard
        if len(cl) != 1 or not (cl[0].is_card(AttackCard) or cl[0].is_card(GrazeCard)):
            return (False, u'请选择一张【弹幕】或者【擦弹】！')
        return (True, u'动之则分，静之则合。无过不及，随曲就伸')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        return (
            u'动之则分，静之则合。无过不及，随曲就伸……|G【%s】|r凭|G太极|r之势，轻松应对。'
        ) % (
            source.ui_meta.char_name,
        )

class LoongPunch:
    # Skill
    name = u'龙拳'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class LoongPunchHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【龙拳】吗？'

class LoongPunchAction:
    def effect_string_before(act):
        if act.type == 'attack':
            return u'|G【%s】|r将内力灌入拳中向|G【%s】|r击出，拳未至，气先行，|G【%s】|r的一张手牌被震飞！' % (
                act.source.ui_meta.char_name,
                act.target.ui_meta.char_name,
                act.target.ui_meta.char_name,
            )
        if act.type == 'graze':
            return u'|G【%s】|r擦过弹幕，随即以拳劲沿着弹幕轨迹回震，|G【%s】|r措手不及，一张手牌掉在了地上。' % (
                act.source.ui_meta.char_name,
                act.target.ui_meta.char_name,
            )

class RiverBehindAwake:
    def effect_string_before(act):
        return u'|G【%s】|r发现自己处境危险，于是强行催动内力护住身体，顺便参悟了太极拳。' % (
            act.target.ui_meta.char_name,
        )

class Meirin:
    # Character
    char_name = u'红美铃'
    port_image = gres.meirin_port
    description = (
        u'|DB我只打盹我不翘班 红美铃 体力：4|r\n\n'
        u'|G龙拳|r：每当你使用一张【弹幕】或【擦弹】时，你可以立即弃置对方的一张手牌。\n\n'
        u'|G背水|r：|B觉醒技|r，回合开始阶段，当你的体力为2或者更少，并且是全场最低时，损失一点体力上限，同时获得|R太极|r技能。\n\n'
        u'|R太极|r：你可将【弹幕】作为【擦弹】，【擦弹】作为【弹幕】使用或打出。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.suika)

class Drunkard:
    # Skill
    name = u'酒鬼'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and act.target is me and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        from ..cards import Card, CardList
        if not (
            cl and len(cl) == 1 and
            cl[0].color == Card.BLACK and
            cl[0].resides_in.type in ('handcard', 'showncard', 'equips')
        ): return (False, u'请选择一张黑色牌！')
        return (True, u'常在地狱走，怎能没有二锅头！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r不知从哪里拿出一瓶酒，大口喝下。' % (
            source.ui_meta.char_name,
        )
        return s

class GreatLandscape:
    # Skill
    name = u'大江山'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class WineGod:
    # Skill
    name = u'醉神'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class WineDream:
    # Skill
    name = u'醉梦'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, 'BUG!')

class WineGodAwake:
    def effect_string_before(act):
        return u'|G【%s】|r找到了自己的本命酒胡芦……喂这样喝没问题吗？' % (
            act.target.ui_meta.char_name,
        )

class Suika:
    # Character
    char_name = u'伊吹萃香'
    port_image = gres.suika_port
    description = (
        u'|DB小小的酒鬼夜行 伊吹萃香 体力：4|r\n\n'
        u'|G大江山|r：|B锁定技|r，当你没有装备武器时，你的攻击范围始终+X，X为你已损失的体力数。\n\n'
        u'|G酒鬼|r：你的出牌阶段，你可以将黑色的手牌或装备牌当【酒】使用。\n\n'
        u'|G醉神|r：|B觉醒技|r，当你装备【伊吹瓢】时，你必须减少1点体力上限，并永久获得技能|R醉梦|r\n\n'
        u'|R醉梦|r：|B锁定技|r，当你解除喝醉状态时，你摸1张牌。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.chen)

class FlyingSkanda:
    # Skill
    name = u'飞翔韦驮天'

    def clickable(game):
        me = game.me
        if me.tags['flying_skanda'] >= me.tags['turn_count']: return False
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        acards = skill.associated_cards
        if len(acards) != 1:
            return (False, u'请选择一张牌！')
        c = acards[0]

        while True:
            if c.is_card(cards.AttackCard): break

            rst = c.is_card(cards.RejectCard)
            rst = rst or c.is_card(cards.DollControlCard)
            rst = (not rst) and issubclass(c.associated_action, cards.InstantSpellCardAction)
            if rst: break

            return (False, u'请选择一张【弹幕】或者除【人形操控】与【好人卡】之外的非延时符卡！')


        if len(target_list) != 2:
            return (False, u'请选择目标（2名玩家）')

        if g.me is target_list[-1]:
            return (False, u'不允许选择自己')
        else:
            return (True, u'喵！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card.associated_cards[0]
        tl = BatchList(act.target_list)

        if card.is_card(cards.AttackCard):
            s = u'弹幕掺了金坷垃，攻击范围一千八！'
        else:
            s = u'符卡掺了金坷垃，一张能顶两张用！'

        return u'|G【%s】|r：“%s|G【%s】|r接招吧！”' % (
            source.ui_meta.char_name,
            s,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

class Chen:
    # Character
    char_name = u'橙'
    port_image = gres.chen_port
    description = (
        u'|DB凶兆的黑喵 橙 体力：4|r\n\n'
        u'|G飞翔韦驮天|r：出牌阶段，你使用的一张【弹幕】或除了【人形操控】与【好人卡】之外的非延时性单体符卡可以额外指定一个目标。每阶段限一次。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.yukari)

class Realm:
    # Skill
    name = u'境界'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, u'BUG!')

class RealmSkipFatetell:
    def effect_string_before(act):
        return u'|G【%s】|r 发动了|G境界|r，跳过了判定阶段。' % (
            act.target.ui_meta.char_name,
        )

class RealmSkipFatetellHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'跳过判定阶段，并弃置一张判定区内的牌')
        else:
            return (False, u'请弃置一张手牌或装备牌，跳过判定阶段')

class RealmSkipDrawCard:
    def effect_string_before(act):
        tl = BatchList(act.pl)
        return u'|G【%s】|r发动了|G境界|r，跳过了摸牌阶段，并抽取了|G【%s】|r的手牌。' % (
            act.target.ui_meta.char_name,
            u'】|r和|G【'.join(tl.ui_meta.char_name),
        )

class RealmSkipDrawCardHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'跳过摸牌阶段，并获得任意1～2名角色的一张手牌')
        else:
            return (False, u'请弃置一张手牌或装备牌，跳过摸牌阶段')

    # choose_players
    def target(tl):
        if not tl:
            return (False, u'请选择1-2名其他玩家，随机出抽取一张手牌')

        return (True, u'跳过摸牌阶段，并获得任意1～2名角色的一张手牌')

class RealmSkipAction:
    # choose_option meta
    choose_option_buttons = ((u'相应区域', True), (u'手牌区', False))
    choose_option_prompt = u'你要将这张卡牌移动到何处？'

    def effect_string_before(act):
        return u'|G【%s】|r发动了|G境界|r，跳过了出牌阶段，并移动了场上的卡牌。' % (
            act.target.ui_meta.char_name,
        )

class RealmSkipActionHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'跳过出牌阶段，并移动场上卡牌')
        else:
            return (False, u'请弃置一张手牌或装备牌，跳过出牌阶段')

    # choose_players
    def target(tl):
        if not tl:
            return (False, u'[出牌]将第一名玩家的装备/判定牌移至第二名玩家的相应区域')

        rst = bool(tl[0].equips or tl[0].fatetell)
        if rst:
            return (len(tl) == 2, u'[出牌]将第一名玩家的装备/判定牌移至第二名玩家的相应区域')
        else:
            return (False, u'第一名玩家没有牌可以让你移动！')

class RealmSkipDropCard:
    def effect_string_before(act):
        return u'|G【%s】|r发动了|G境界|r，跳过了弃牌阶段。' % (
            act.target.ui_meta.char_name,
        )

class RealmSkipDropCardHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置一张牌，跳过弃牌阶段')
        else:
            return (False, u'弃置一张牌，跳过弃牌阶段')

class Yukari:
    # Character
    char_name = u'八云紫'
    port_image = gres.yukari_port
    description = (
        u'|DB永远17岁 八云紫 体力：4|r\n\n'
        u'|G境界|r：你可以弃一张牌跳过你的一个阶段（回合开始和回合结束阶段除外）\n'
        u'|B|R>>|r 若你跳过判定阶段，你可以弃置你的判定区里的一张牌\n'
        u'|B|R>>|r 若你跳过摸牌阶段，你可以获得任意1～2名角色的一张手牌；\n'
        u'|B|R>>|r 若你跳过出牌阶段，你可以将一名角色装备区或判定区的一张牌移动到另一名角色的装备区或判定区相同位置（不可替换原装备）或交给其他任意一名角色。'
    )

# ----------
from options import options
if options.testing:
    __metaclass__ = gen_metafunc(characters.dummy)

    class Dummy:
        # Character
        char_name = u'机器人'
        port_image = gres.dummy_port
        description = (
            u'|DB河童工厂的残次品 机器人 体力：5|r\n\n'
            u'|G我很强壮|r：嗯，很强壮……'
        )

del options

# ----------
__metaclass__ = gen_metafunc(characters.sakuya)

class Sakuya:
    # Character
    char_name = u'十六夜咲夜'
    port_image = gres.sakuya_port
    description = (
        u'|DB完全潇洒的PAD长 十六夜咲夜 体力：4|r\n\n'
        u'|G月时计|r：|B锁定技|r，在你的判定阶段开始前，你执行一个额外的出牌阶段。\n\n'
        u'|G飞刀|r：你可以将一张装备牌当【弹幕】使用或打出。你以此法使用【弹幕】时无距离限制。'
    )

class FlyingKnife:
    # Skill
    name = u'飞刀'

    def clickable(g):
        me = g.me

        try:
            act = g.action_stack[-1]
        except IndexError:
            return False

        if not (me.cards or me.showncards or me.equips): return False
        if not isinstance(act, (actions.ActionStage, cards.UseAttack, cards.BaseUseGraze, cards.DollControl)):
            return False

        if act.target is not g.me: return False

        return True

    def is_complete(g, cl):
        skill = cl[0]
        assert skill.is_card(characters.sakuya.FlyingKnife)
        cl = skill.associated_cards
        if len(cl) != 1 or not issubclass(cl[0].associated_action, cards.WearEquipmentAction):
            return (False, u'请选择一张装备牌！')
        return (True, '快看！灰出去了！')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        rst, reason = is_complete(g, cl)
        if not rst:
            return rst, reason
        else:
            return cards.AttackCard.ui_meta.is_action_valid(g, cl, target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r将|G%s|r制成了|G飞刀|r，向|G【%s】|r掷去！' % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.char_name,
        )
        return s


class LunaClock:
    # Skill
    name = u'月时计'

    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, u'BUG!')

# ----------
__metaclass__ = gen_metafunc(characters.sanae)

class Sanae:
    # Character
    char_name = u'东风谷早苗'
    port_image = gres.sanae_port
    description = (
        u'|DB常识满满的现人神 东风谷早苗 体力：3|r\n\n'
        u'|G御神签|r：出牌阶段，你可以指定一名角色，然后让其摸取等同于其残机数与场上残机数最多的角色的残机数之差的牌（至多4张，至少1张）。每阶段限一次。\n\n'
        u'|G奇迹|r：当你受到一次伤害，你可以指定任意一名角色摸X张牌（X为你已损失的体力值）。'
    )


class DrawingLotAction:
    def effect_string(act):
        return u'大吉！|G【%s】|r脸上满满的满足感，摸了%d张牌。' % (
            act.target.ui_meta.char_name,
            act.amount,
        )


class DrawingLot:
    name = u'御神签'
    def clickable(g):
        me = g.me

        try:
            act = g.action_stack[-1]
        except IndexError:
            return False

        if not isinstance(act, actions.ActionStage):
            return False

        if act.target is not g.me: return False
        t = act.target.tags
        if t['turn_count'] <= t['drawinglot_tag']: return False

        return True

    def effect_string(act):
        return u'|G【%s】|r给|G【%s】|r抽了一签……' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌！')

        return (True, u'一定是好运气的！')


class Miracle:
    # Skill
    name = u'奇迹'
    def clickable(game):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, u'BUG!')


class MiracleAction:
    def effect_string(act):
        return u'|G【%s】|r说，要有|G奇迹|r，于是|G【%s】|r就摸了%d张牌。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            act.amount,
        )


class MiracleHandler:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'奇迹：请选择1名体力不满的玩家')

        return (True, u'奇迹！')

# ----------
__metaclass__ = gen_metafunc(characters.akari)

class Akari:
    # Character
    char_name = u'随机角色'
    port_image = gres.akari_port
    description = (
        u'|DB会是谁呢 随机角色 体力：?|r\n\n'
        u'|G阿卡林|r：消失在画面里的能力。在开局之前，没有人知道这是谁。'
    )

# ----------
__metaclass__ = gen_metafunc(characters.seiga)


class Seiga:
    # Character
    char_name = u'霍青娥'
    port_image = gres.seiga_port
    description = (
        u'|DB僵尸别跑 霍青娥 体力：4|r\n\n'
        u'|G邪仙|r：你的回合内，你可以将一张对自己生效、单体目标或者群体目标的卡牌交给任意一名玩家，并以该玩家的身份立即使用。\n'
        u'|B|R>> |r以此方法使用弹幕时，弹幕的“一回合一次”的限制由你来承担\n'
        u'|B|R>> |r在结算的过程中，“选择对方的牌”、“是否发动技能”操作均由你来完成。\n'
        u'|B|R>> |r在结算的过程中，你可以选择跳过指向多人的卡牌效果结算。'
        
        # u'|G穿墙|r：当你成为可指向多人的卡牌、技能的目标时，你可以使该效果无效并摸一张牌。'
    )


class Passthru:
    # Skill
    name = u'穿墙'

    def clickable(g):
        return False

    def is_action_valid(g, cl, target_list):
        return (False, u'BUG!')


class PassthruAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G穿墙|r技能，跳过了卡牌效果，并摸1张牌。' % (
            act.source.ui_meta.char_name,
        )


class PassthruHandler:
    # choose_option meta
    choose_option_buttons = ((u'跳过并摸牌', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【穿墙】技能吗？'


class HeterodoxyHandler:
    # choose_option meta
    choose_option_buttons = ((u'跳过结算', True), (u'正常结算', False))
    choose_option_prompt = u'你要跳过当前的卡牌结算吗？'


class HeterodoxySkipAction:
    def effect_string(act):
        return u'|G【%s】|r跳过了卡牌效果的结算' % (
            act.source.ui_meta.char_name,
        )


class HeterodoxyAction:
   def ray(act):
       return [(act.source, act.target_list[0])]


class Heterodoxy:
    # Skill
    name = u'邪仙'
    custom_ray = True

    def clickable(g):
        if not my_turn(g):
            return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def effect_string(act):
        return u'|G【%s】|r发动了邪仙技能，以|G【%s】|r的身份使用了卡牌' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def is_action_valid(g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, u'请选择一张牌')

        card = acards[0]

        permitted = {
            't_Self', 't_One', 't_OtherOne', 't_DollControl',
            't_All', 't_AllInclusive',
        }

        tname = card.target.__name__
        if tname not in permitted:
            return (False, u'请的选择对自己生效、单体、群体卡牌！')

        if not tl:
            return (False, u'请选择一名玩家作为卡牌发起者')

        victim = tl[0]
        _tl, valid = card.target(g, victim, tl[1:])
        return card.ui_meta.is_action_valid(g, [card], _tl)

        # can't reach here
        # return (True, u'僵尸什么的最萌了！')

# -----END CHARACTERS UI META-----

# -----BEGIN TAGS UI META-----
tags = {}
def tag_metafunc(clsname, bases, _dict):
    data = DataHolder.parse(_dict)
    tags[clsname] = data

__metaclass__ = tag_metafunc

class attack_num:
    tag_anim = lambda p: gres.tag_attacked
    display = lambda p, v: v <= 0 and G().current_turn is p
    description = u'该玩家在此回合不能再使用【弹幕】了'

class wine:
    tag_anim = lambda p: gres.tag_wine
    display = lambda p, v: v
    description = u'喝醉了…'

class flan_cs:
    tag_anim = lambda p: gres.tag_flandrecs
    display = lambda p, v: v
    description = u'玩坏你哦！'

class lunaclock:
    tag_anim = lambda p: gres.tag_lunaclock
    display = lambda p, v: v
    description = u'咲夜的时间！'

# -----END TAGS UI META-----
