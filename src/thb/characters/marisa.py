# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import LaunchCard, UserAction, migrate_cards, random_choose_card
from thb.cards.classes import AttackCard, Skill, TreatAs, VirtualCard, t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --

# 虚拟卡牌，复制「弹幕」的信息
class Daze(TreatAs, VirtualCard):
    treat_as = AttackCard

# 「借走」的逻辑
class BorrowAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        g = self.game

        # 选择目标的一张牌
        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards', 'equips')))
        # 如果没选，那么随机选一张
        c = c or random_choose_card(g, [tgt.cards, tgt.showncards])
        if not c: return False
        # 向发动者展示这张牌，并移动到发动者的手牌区
        src.reveal(c)
        migrate_cards([c], src.cards)
        # 标记技能已经用过了
        src.tags['borrow_tag'] = src.tags['turn_count']

        # 目标选择是否向发动者发动「视为使用弹幕」的动作
        if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            g.process_action(LaunchCard(tgt, [src], Daze(tgt), bypass_check=True))

        return True

    def is_valid(self):
        src = self.source
        tgt = self.target
        if src.tags['turn_count'] <= src.tags['borrow_tag']:
            return False

        if not (tgt.cards or tgt.showncards or tgt.equips):
            return False

        return True


class Borrow(Skill):
    # 技能主动发动时需要执行的动作，就是上面的那个
    associated_action = BorrowAction
    skill_category = ['character', 'active']
    # 技能的目标，这里是除了你之外的一个玩家
    target = t_OtherOne

    def check(self):
        if self.associated_cards: return False
        return True


@register_character_to('common')
class Marisa(Character):
    skills = [Borrow]
    maxlife = 4
