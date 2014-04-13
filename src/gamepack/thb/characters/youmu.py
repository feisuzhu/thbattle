# -*- coding: utf-8 -*-

from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import ActionStage, Damage, DropCards, GenericAction, migrate_cards, random_choose_card, UserAction, MaxLifeChange, MigrateCardsTransaction
from ..cards import Skill, Attack, LaunchGraze, HakuroukenCard, RoukankenCard, WearEquipmentAction, BaseDuel, t_None, UseAttack, Heal, t_Self, AttackCardHandler
from ..inputlets import ChooseIndividualCardInputlet
from utils import classmix


class MijincihangzhanAttack(Attack):
    pass

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

        with MigrateCardsTransaction() as trans:
            if cat == 'weapon':
                weapons = [e for e in equips if e.equipment_category == 'weapon']
                if len(weapons) > 1:
                    e = user_input(
                        [target], ChooseIndividualCardInputlet(self, weapons),
                    ) or random_choose_card([weapons])
                    migrate_cards([e], g.deck.droppedcards, trans=trans)

            else:
                for oc in equips:
                    if oc.equipment_category == cat:
                        migrate_cards([oc], g.deck.droppedcards, trans=trans)
                        break

            migrate_cards([card], target.equips, trans=trans)

        return True


class YoumuHandler(EventHandler):
    execute_before = ('ScarletRhapsodySwordHandler', 'LaevateinHandler', 'HouraiJewelHandler')
    execute_after = ('AttackCardHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, Attack):
                if not act.source.has_skill(Mijincihangzhan): return act
                act.__class__ = classmix(MijincihangzhanAttack, act.__class__)
                act.graze_count = 0
            elif isinstance(act, BaseDuel):
                if not isinstance(act, MijincihangzhanDuelMixin):
                    act.__class__ = classmix(MijincihangzhanDuelMixin, act.__class__)
            elif isinstance(act, WearEquipmentAction):
                if not act.source.has_skill(Nitoryuu): return act
                act.__class__ = YoumuWearEquipmentAction

        elif evt_type == 'action_apply' and isinstance(act, ActionStage):
            p = act.target
            p.tags['attack_num'] += p.tags.get('nitoryuu_tag', False)

        elif evt_type == 'card_migration':
            def weapons(cards):
                return [c for c in cards
                        if c.equipment_category == 'weapon']

            act, cards, _from, to = arg = act

            for cl in (_from, to):
                if cl.type != 'equips': continue
                p = cl.owner
                if p.has_skill(Nitoryuu):
                    active = len(weapons(p.equips)) >= 2
                    oactive = p.tags.get('nitoryuu_tag', False)
                    p.tags['attack_num'] += active - oactive
                    p.tags['nitoryuu_tag'] = active

            return arg

        elif evt_type == 'attack_aftergraze':
            act, rst = arg = act
            if rst: return arg
            if not isinstance(act, MijincihangzhanAttack): return arg

            g = Game.getgame() 
            return act, not g.process_action(LaunchGraze(act.target))

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

    def is_valid(self):
        return self.source.tags.get('nitoryuu_tag', False)


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
