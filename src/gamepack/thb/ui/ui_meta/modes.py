# -*- coding: utf-8 -*-

from gamepack.thb import thb3v3, thbidentity, thbraid, thbkof, thbfaith, thbcp3, thb2v2
from gamepack.thb.ui.resource import resource as gres

from .common import gen_metafunc, card_desc, my_turn
from .common import limit1_skill_used, passive_clickable, passive_is_action_valid

# -----BEGIN THB3v3 UI META-----
__metaclass__ = gen_metafunc(thb3v3)


class THBattle:
    name = u'符斗祭 - 3v3'
    logo = gres.thblogo_3v3
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

    from gamepack.thb.ui.view import THBattleUI as ui_class  # noqa

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

# -----BEGIN THBCP3 UI META-----
__metaclass__ = gen_metafunc(thbcp3)


class THBattleCP3:
    name = u'符斗祭 - CP大战'
    logo = gres.thblogo_cp3
    description = (
        u'|R游戏人数|r：6人\n'
        u'\n'
        u'阵营分为3对CP，每个阵营2名玩家，交错入座。\n'
        u'由ROLL点最高的人开始，按照顺时针顺序选将。\n'
        u'选将完成由ROLL点最高的玩家开始行动。\n'
        u'ROLL点最高的玩家开局摸3张牌，其余玩家开局摸4张牌。\n'
        u'当一名玩家被击坠时，将其全部手牌与装备交给其CP。\n'
        u'\n'
        u'|R胜利条件|r：击坠所有其它阵营玩家。'
    )

    from gamepack.thb.ui.view import THBattleCP3UI as ui_class  # noqa

    T = thbcp3.Identity.TYPE
    identity_table = {
        T.HIDDEN: u'？',
        T.CP_A:   u'CP A',
        T.CP_B:   u'CP B',
        T.CP_C:   u'CP C',
    }

    identity_color = {
        T.HIDDEN: u'blue',
        T.CP_A:   u'blue',
        T.CP_B:   u'orange',
        T.CP_C:   u'green',
    }

    del T

# -----END THBCP3 UI META-----


# -----BEGIN THBKOF UI META-----
__metaclass__ = gen_metafunc(thbkof)


class THBattleKOF:
    name = u'符斗祭 - KOF模式'
    logo = gres.thblogo_kof
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

    from gamepack.thb.ui.view import THBattleKOFUI
    ui_class = THBattleKOFUI

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
    logo = gres.thblogo_8id
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

    from gamepack.thb.ui.view import THBattleIdentityUI
    ui_class = THBattleIdentityUI

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


class THBattleIdentity5:
    name = u'符斗祭 - 标准5人身份场'
    logo = gres.thblogo_5id
    description = (
        u'|R游戏人数|r：5人\n'
        u'\n'
        u'|R身份分配|r：1|!RBOSS|r、1|!O道中|r、1|!G黑幕|r、2|!B城管|r\n'
        u'\n'
        u'|!RBOSS|r：游戏开局时展示身份。胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        u'\n'
        u'|!O道中|r：胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        u'\n'
        u'|!B城管|r：胜利条件为击坠|!RBOSS|r。当|!B城管|rMISS时，击坠者摸3张牌。\n'
        u'\n'
        u'|!G黑幕|r：胜利条件为在除了|!RBOSS|r的其他人都MISS的状况下击坠|!RBOSS|r。\n'
        u'\n'
        u'玩家的身份会在MISS后公开。|!RBOSS|r的身份会在开局的时候公开。'
    )

    from gamepack.thb.ui.view import THBattleIdentity5UI
    ui_class = THBattleIdentity5UI

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


# -----BEGIN THBRaid UI META-----
__metaclass__ = gen_metafunc(thbraid)


class THBattleRaid:
    name = u'符斗祭 - 异变模式'
    logo = gres.thblogo_raid

    from gamepack.thb.ui.view import THBattleRaidUI
    ui_class = THBattleRaidUI

    T = thbraid.Identity.TYPE
    identity_table = {
        T.HIDDEN:   u'？',
        T.MUTANT:   u'异变',
        T.ATTACKER: u'解决者',
    }

    identity_color = {
        T.HIDDEN:   u'blue',
        T.MUTANT:   u'red',
        T.ATTACKER: u'blue',
    }

    del T

    description = (
        u"|R势力|r： 异变（1人） vs 解决者（3人）\n"
        u"\n"
        u"|R信仰|r：所有人都有额外的“信仰”，信仰使用卡牌做标记，需向他人展示。信仰可以在自己的出牌阶段前与手牌做交换。交换后进入明牌区。每对其他玩家造成一点伤害时，获得一点。信仰上限为5点。异变在每轮开始时获得一点信仰，解决者不获得。\n"
        u"\n"
        u"|R距离|r：所有人之间的默认距离为1\n"
        u"\n"
        u"|R出牌顺序|r：\n"
        u"(异变->解决者1->异变->解决者2->异变->解决者3)->……\n"
        u"异变变身后, 立即终止卡牌结算，从异变开始：\n"
        u"(异变->解决者1->解决者2->解决者3)->……\n"
        u"解决者们可以任意决定行动顺序，但是每轮一个解决者仅能行动一次。\n"
        u"当所有在场的玩家结束了各自回合之后，算作一轮。\n"
        u"\n"
        u"|R异变变身|r：当1阶段的异变体力值变化成小于等于默认体力上限的一半时，变身成2阶段，获得2阶段技能，体力上限减少默认体力上限的一半，弃置判定区的所有牌。异变变身时，所有解决者各获得1点信仰。\n"
        u"\n"
        u"|R卡牌|r：牌堆中没有【罪袋】和【八卦炉】\n"
        u"\n"
        u"|R摸牌|r：游戏开始时，3个解决者每人摸4张牌，异变摸6张。当任意解决者阵亡时，弃置所有信仰，其他存活的解决者可以选择立即在牌堆里摸1张牌。\n"
        u"\n"
        u"|R解决者额外技能|r：\n"
        u"|G合作|r：在你的出牌阶段，你可以将至多两张手牌交给其他的一名解决者。收到牌的解决者需交还相同数量的手牌，交换后进入明牌区。一回合一次。\n"
        u"|G保护|r：当其他解决者受到伤害时，如果该解决者的体力是全场最低之一，你可以使用1点信仰防止此伤害。若如此做，你承受相同数量的体力流失，并且异变获得一点信仰。\n"
        u"|G招架|r：若你受到了2点及以上/致命的伤害时，你可以使用2点信仰使伤害-1。在 保护 之前结算。\n"
        u"|G1UP|r：|B限定技|r，你可以使用3点信仰使已经阵亡的解决者重新上场。重新上场的解决者回复3点体力，算作当前回合没有行动。"
    )


class DeathHandler:
    # choose_option
    choose_option_buttons = ((u'摸一张', True), (u'不摸牌', False))
    choose_option_prompt = u'你要摸一张牌吗？'


class CollectFaith:
    def effect_string(act):
        if not act.succeeded: return None
        if not len(act.cards): return None
        s = u'、'.join(card_desc(c) for c in act.cards)
        return u'|G【%s】|r收集了%d点信仰：%s' % (
            act.target.ui_meta.char_name, len(act.cards), s,
        )


class CooperationAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'OK，就这些了')
        else:
            return (False, u'请选择%d张手牌交还…' % act.ncards)


class Cooperation:
    # Skill
    name = u'合作'

    def clickable(g):
        if not my_turn(): return False
        if limit1_skill_used('cooperation_tag'): return False
        return True

    def is_action_valid(g, cl, target_list):
        acards = cl[0].associated_cards
        if not acards:
            return (False, u'请选择希望交换的手牌')

        if len(acards) > 2:
            return (False, u'最多选择两张')

        if any(c.resides_in.type not in ('cards', 'showncards') for c in acards):
            return (False, u'只能选择手牌！')

        if len(target_list) != 1:
            return (False, u'请选择一名解决者')

        return (True, u'合作愉快~')

    def effect_string(act):
        return u'|G【%s】|r与|G【%s】|r相互合作，交换了手牌。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class Protection:
    # Skill
    name = u'保护'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ProtectionAction:
    def effect_string(act):
        return u'|G【%s】|r帮|G【%s】|r承受了伤害。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class ProtectionHandler:
    # choose_option
    choose_option_buttons = ((u'保护', True), (u'不保护', False))

    def choose_option_prompt(act):
        return u'你要使用1点信仰承受此次的%d点伤害吗？' % act.dmgact.amount


class Parry:
    # Skill
    name = u'招架'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ParryAction:
    def effect_string(act):
        return u'|G【%s】|r使用了|G招架|r，减免了1点伤害。' % (
            act.target.ui_meta.char_name,
        )


class ParryHandler:
    # choose_option
    choose_option_buttons = ((u'招架', True), (u'不招架', False))
    choose_option_prompt = u'你要使用2点信仰减免1点伤害吗？'


class OneUp:
    # Skill
    name = '1UP'

    def clickable(g):
        if not my_turn(): return False
        return len(g.me.faiths) >= 3

    def is_action_valid(g, cl, target_list):
        acards = cl[0].associated_cards
        if len(acards):
            return (False, u'请不要选择牌！')

        if not (len(target_list) == 1 and target_list[0].dead):
            return (False, u'请选择一名已经离场的玩家')

        return (True, u'神说，你不能在这里死去')

    def effect_string(act):
        return u'|G【%s】|r用3点信仰换了一枚1UP，贴到了|G【%s】|r的身上。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class OneUpAction:
    update_portrait = True


class FaithExchange:
    def effect_string_before(act):
        return u'|G【%s】|r正在交换信仰牌……' % (
            act.target.ui_meta.char_name,
        )

    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'OK，就这些了')
        else:
            return (False, u'请选择%d张手牌作为信仰…' % act.amount)


class RequestAction:
    # choose_option
    choose_option_buttons = ((u'行动', True), (u'等一下', None))
    choose_option_prompt = u'你要行动吗？'


class GetFaith:
    # choose_option
    choose_option_buttons = ((u'我要信仰', True), (u'给其他人', None))
    choose_option_prompt = u'你要获得一点信仰吗（只有一人可以获得）？'

# -----END THBRaid UI META-----

# -----BEGIN THBFaith UI META-----
__metaclass__ = gen_metafunc(thbfaith)


class THBattleFaith:
    name = u'符斗祭 - 信仰争夺战'
    logo = gres.thblogo_faith
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

    from gamepack.thb.ui.view import THBattleFaithUI as ui_class  # noqa

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

# -----BEGIN THBFaith UI META-----
__metaclass__ = gen_metafunc(thb2v2)


class THBattle2v2:
    name = u'符斗祭 - 2v2'
    logo = gres.kokoro_port
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

    from gamepack.thb.ui.view import THBattle2v2UI as ui_class  # noqa

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


class THBattle2v2Ban:
    choose_girl_text = u'请选择不希望出现在选人画面中的人物'


class HeritageHandler:
    # choose_option
    choose_option_buttons = ((u'获取队友的所有牌', 'inherit'), (u'摸两张牌', 'draw'))
    choose_option_prompt  = u'队友MISS，请选择你的动作'

# -----END THBFaith UI META-----
