# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import ActionStage, Damage, DropCards, MigrateCardsTransaction, UserAction
from thb.actions import migrate_cards, random_choose_card
from thb.cards import Attack, BaseDuel, LaunchGraze, Skill, UseAttack, t_None, t_Self
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseIndividualCardInputlet
from utils import classmix


# -- code --
class MijincihangzhanAttack(Attack):
    pass


class MijincihangzhanDuelMixin(object):
    # 迷津慈航斩 弹幕战
    def apply_action(self):
        g = Game.getgame()
        source = self.source
        target = self.target

        d = (source, target)
        while True:
            d = (d[1], d[0])
            if d[1].has_skill(Nitoryuu):
                if not (
                    g.process_action(UseAttack(d[0])) and
                    g.process_action(UseAttack(d[0]))
                ): break
            else:
                if not g.process_action(UseAttack(d[0])): break

        g.process_action(Damage(d[1], d[0], amount=1))
        return d[1] is source


class NitoryuuWearEquipmentAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        tgt = self.target
        g = Game.getgame()

        weapons = [e for e in tgt.equips if e.equipment_category == 'weapon']
        if len(weapons) > 1:
            e = user_input([tgt], ChooseIndividualCardInputlet(self, weapons))
            e = e or random_choose_card([weapons])
            g.process_action(DropCards(tgt, tgt, [e]))

        migrate_cards([card], tgt.equips)

        return True


class NitoryuuWearEquipmentHandler(EventHandler):
    interested = ('wear_equipment',)

    def handle(self, evt_type, arg):
        we, tgt, c, rst = arg
        if not evt_type == 'wear_equipment': return arg
        if not tgt.has_skill(Nitoryuu): return arg
        if 'equipment' not in c.category: return arg
        if c.equipment_category != 'weapon': return arg

        g = Game.getgame()
        g.process_action(NitoryuuWearEquipmentAction(tgt, tgt, c))
        return we, tgt, c, 'handled'


class YoumuHandler(EventHandler):
    interested = ('action_apply', 'action_before', 'attack_aftergraze', 'card_migration')
    execute_before = ('ScarletRhapsodySwordHandler', 'LaevateinHandler', 'HouraiJewelHandler')
    execute_after = ('VitalityHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, Attack):
                if not act.source.has_skill(Mijincihangzhan): return act
                act.__class__ = classmix(MijincihangzhanAttack, act.__class__)
                act.graze_count = 0
            elif isinstance(act, BaseDuel):
                if not isinstance(act, MijincihangzhanDuelMixin):
                    act.__class__ = classmix(MijincihangzhanDuelMixin, act.__class__)

        elif evt_type == 'action_apply' and isinstance(act, ActionStage):
            p = act.target
            p.tags['vitality'] += bool(p.has_skill(Nitoryuu) and self.weapons(p) >= 2)

        elif evt_type == 'card_migration':

            act, cards, _from, to, _ = arg = act

            for cl in (_from, to):
                if cl.type != 'equips': continue
                p = cl.owner
                if not p.has_skill(Nitoryuu): continue

                n = self.weapons(p)
                dn = len(cards)

                if cl is _from and (dn + n) >= 2 and n <= 1 and any(getattr(c, 'equipment_category', None) == 'weapon' for c in cards):
                    adjust = -1
                elif cl is to and (n - dn) <= 1 and n >= 2:
                    adjust = 1
                else:
                    adjust = 0

                p.tags['vitality'] += adjust

            return arg

        elif evt_type == 'attack_aftergraze':
            act, rst = arg = act
            if rst: return arg
            if not isinstance(act, MijincihangzhanAttack): return arg

            g = Game.getgame()
            return act, not g.process_action(LaunchGraze(act.target))

        return act

    @staticmethod
    def weapons(p):
        return sum([c.equipment_category == 'weapon' for c in p.equips])


class Mijincihangzhan(Skill):
    # 迷津慈航斩
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class Nitoryuu(Skill):
    # 二刀流
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None

    def check(self):
        return not self.associated_cards


@register_character_to('common')
class Youmu(Character):
    skills = [Mijincihangzhan, Nitoryuu]
    eventhandlers_required = [YoumuHandler, NitoryuuWearEquipmentHandler]
    maxlife = 4
