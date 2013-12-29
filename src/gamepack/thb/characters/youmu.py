# -*- coding: utf-8 -*-

from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import ActionStage, Damage, DropCards, GenericAction, migrate_cards, random_choose_card, UserAction, MaxLifeChange
from ..cards import Skill, Attack, LaunchGraze, HakuroukenCard, RoukankenCard, WearEquipmentAction, BaseDuel, t_None, UseAttack, Heal, t_Self
from ..inputlets import ChooseIndividualCardInputlet
from utils import classmix


class MijincihangzhanAttack(Attack):
    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target

        for i in xrange(2):
            graze_action = LaunchGraze(target)
            if not g.process_action(graze_action):
                break
        else:
            return False

        g.process_action(Damage(source, target, amount=self.damage))
        return True


class MijincihangzhanDuelMixin(object):
    # 迷津慈航斩 弹幕战
    def apply_action(self):
        g = Game.getgame()
        source = self.source
        target = self.target

        d = (source, target)
        dmg = (self.source_damage, self.target_damage)
        while True:
            d = (d[1], d[0])
            dmg = (dmg[1], dmg[0])
            if d[1].has_skill(Nitoryuu):
                if not (
                    g.process_action(UseAttack(d[0])) and
                    g.process_action(UseAttack(d[0]))
                ): break
            else:
                if not g.process_action(UseAttack(d[0])): break

        g.process_action(Damage(d[1], d[0], amount=dmg[1]))
        return d[1] is source


class XianshiwangzhiAwake(GenericAction):
    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        tgt.skills.append(Xianshiwangzhi)
        tgt.tags['attack_num'] += 1
        g.process_action(MaxLifeChange(tgt, tgt, 1))
        g.process_action(Heal(tgt, tgt, 1))
        return True


class YoumuWearEquipmentAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card
        target = self.target
        equips = target.equips
        g = Game.getgame()
        cat = card.equipment_category
        if cat == 'weapon':
            weapons = [e for e in equips if e.equipment_category == 'weapon']
            if len(weapons) > 1:
                e = user_input(
                    [target], ChooseIndividualCardInputlet(self, weapons),
                ) or random_choose_card([weapons])
                g.process_action(DropCards(target, [e]))
                weapons.remove(e)

            weapons.append(card)
            cls = set([i.__class__ for i in weapons])
            l = set([HakuroukenCard, RoukankenCard])
            if cls == l and not target.has_skill(Xianshiwangzhi):
                g.process_action(XianshiwangzhiAwake(target, target))

        else:
            for oc in equips:
                if oc.equipment_category == cat:
                    g.process_action(DropCards(target, [oc]))
                    break

        migrate_cards([card], target.equips)
        return True


class YoumuHandler(EventHandler):
    execute_before = ('ScarletRhapsodySwordHandler', 'LaevateinHandler', 'HouraiJewelHandler')
    execute_after = ('AttackCardHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, Attack):
                if not act.source.has_skill(Mijincihangzhan): return act
                act.__class__ = classmix(MijincihangzhanAttack, act.__class__)
            elif isinstance(act, BaseDuel):
                if not isinstance(act, MijincihangzhanDuelMixin):
                    act.__class__ = classmix(MijincihangzhanDuelMixin, act.__class__)
            elif isinstance(act, WearEquipmentAction):
                if not act.source.has_skill(Nitoryuu): return act
                act.__class__ = YoumuWearEquipmentAction
            elif isinstance(act, ActionStage):
                a = act.target
                if not a.has_skill(Xianshiwangzhi): return act
                a.tags['attack_num'] += 1

        return act


class NitoryuuDropWeapon(UserAction):
    def apply_action(self):
        tgt = self.target
        equips = tgt.equips
        weapons = [e for e in equips if e.equipment_category == 'weapon']
        e = user_input(
            [tgt], ChooseIndividualCardInputlet(self, weapons),
        ) or random_choose_card([weapons])
        g = Game.getgame()
        g.process_action(DropCards(tgt, [e]))

        return True


class Mijincihangzhan(Skill):
    # 迷津慈航斩
    associated_action = None
    target = t_None


class Nitoryuu(Skill):
    # 二刀流
    associated_action = NitoryuuDropWeapon
    target = t_Self

    def check(self):
        return not self.associated_cards


class Xianshiwangzhi(Skill):
    # 现世妄执
    associated_action = None
    target = t_None


@register_character
class Youmu(Character):
    skills = [Mijincihangzhan, Nitoryuu]
    eventhandlers_required = [YoumuHandler]
    maxlife = 4
