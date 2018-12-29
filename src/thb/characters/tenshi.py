# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import Damage, DrawCards, Fatetell, GenericAction, LaunchCard, UserAction
from thb.actions import ask_for_action, migrate_cards
from thb.cards.base import Card, Skill
from thb.cards.classes import t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --

# 「抖M」技能，对应郭嘉的「遗计」
class Masochist(Skill):
    # 技能没有附带的动作，仅被动触发
    associated_action = None
    # 技能的分类
    skill_category = ['character', 'passive']
    # 技能的目标，因为没有附带动作所以也没有目标
    target = t_None


# 「抖M」技能动作
class MasochistAction(UserAction):
    # 在请求玩家输入后，不要自动将牌面告知其他玩家
    no_reveal = True
    # 卡牌的使用场景是「交给其他人」
    card_usage = 'handover'

    # 参数分别是动作目标（自己）和受到伤害的数量
    def __init__(self, target, n):
        self.source, self.target, self.amount = target, target, n

    # 动作的逻辑
    def apply_action(self):
        g = self.game
        tgt = self.target
        # 构造自己摸两张牌的动作
        a = DrawCards(tgt, self.amount * 2)
        # 执行这个动作
        g.process_action(a)
        self.cards = cards = a.cards
        n = len(cards)
        # 如果牌还没有送完，继续执行
        while n > 0:
            # 选取其他没有阵亡的角色
            pl = [p for p in g.players if not p.dead]
            pl.remove(tgt)
            if not pl:
                return True

            # 玩家选择给出的牌和目标玩家
            _, rst = ask_for_action(self, [tgt], ('cards',), pl)
            if not rst:
                return True

            cl, pl = rst
            # 告知目标牌面
            pl[0].player.reveal(cl)
            # 转移卡牌
            migrate_cards(cl, pl[0].cards)
            n -= len(cl)

        return True

    # ask_for_action 函数用的条件，给出的牌必须是拿到的牌
    def cond(self, cl):
        cards = self.cards
        return all(c in cards for c in cl)

    # ask_for_action 函数用的条件，给出的牌必须是拿到的牌
    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


# 「抖M」技能的事件触发逻辑
class MasochistHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        # 当受到伤害后
        if evt_type == 'action_after' and isinstance(act, Damage):
            # 如果目标没有阵亡，且身负「抖M」技能
            tgt = act.target
            if tgt.dead: return act
            if not tgt.has_skill(Masochist): return act
            if not act.amount: return act

            # 选择是否发动
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            # 实际发动技能
            self.game.process_action(MasochistAction(tgt, act.amount))

        return act


# 「绯想」技能，对应郭嘉「天妒」
# 锁定技，距离1以内的角色的红色判定牌置入弃牌堆时，你获得之。
class ScarletPerception(Skill):
    distance = 1
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class ScarletPerceptionAction(GenericAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        migrate_cards([self.card], self.source.cards, is_bh=True)
        return True


class ScarletPerceptionHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        # 在判定结束后
        if evt_type == 'action_after' and isinstance(act, Fatetell):
            tgt = act.target

            # 如果牌的颜色是红色，而且没有在某个牌区内（不属于任何人，或者牌堆）
            if act.card.color != Card.RED: return act
            g = self.game
            if not act.card.detached:
                return act

            # 寻找场内身负「绯想」技能的人
            g = self.game
            pl = [p for p in g.players if p.has_skill(ScarletPerception) and not p.dead]
            assert len(pl) <= 1

            if pl:
                p = pl[0]
                dist = LaunchCard.calc_distance(p, ScarletPerception(p))
                # 若满足距离限制
                if dist.get(tgt, 1) <= 0:
                    # 执行获得牌的动作
                    g.process_action(ScarletPerceptionAction(p, tgt, act.card))

        return act


# 「比那名居天子」人物
@register_character_to('common')
class Tenshi(Character):
    # 人物技能
    skills = [Masochist, ScarletPerception]
    # 需要的事件处理器
    eventhandlers = [MasochistHandler, ScarletPerceptionHandler]
    # 最大体力
    maxlife = 3
