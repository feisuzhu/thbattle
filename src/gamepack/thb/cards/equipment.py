# -*- coding: utf-8 -*-

from .base import *
from ..skill import *
from ..actions import *

from . import basic

class WearEquipmentAction(UserAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card
        target = self.target
        equips = target.equips
        for oc in equips:
            if oc.equipment_category == card.equipment_category:
                migrate_cards([oc], g.deck.droppedcards)
                break
        migrate_cards([card], target.equips)
        return True

@register_eh
class EquipmentTransferHandler(EventHandler):
    def handle(self, evt, args):
        if evt == 'card_migration':
            act, cards, _from, to = args
            if _from.type == CardList.EQUIPS:
                for c in cards:
                    _from.owner.skills.remove(c.equipment_skill)

            if to.type == CardList.EQUIPS:
                for c in cards:
                    to.owner.skills.append(c.equipment_skill)

        return args

class ShieldSkill(Skill):
    associated_action = None
    target = None

class OpticalCloakSkill(ShieldSkill): # just a tag
    pass

class OpticalCloak(FatetellAction, GenericAction):
    # 光学迷彩
    def __init__(self, target, ori):
        self.target = target
        self.ori_usegraze = ori

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        ft = Fatetell(target, lambda card: card.suit in (Card.HEART, Card.DIAMOND))
        g.process_action(ft)
        if ft.succeeded:
            return True
        else:
            return g.process_action(self.ori_usegraze)

@register_eh
class OpticalCloakHandler(EventHandler):
    def handle(self, evt_type, act):
        from .basic import UseGraze
        if evt_type == 'action_before' and isinstance(act, UseGraze) and not hasattr(act, 'oc_tag'):
            target = act.target
            if target.has_skill(OpticalCloakSkill):
                # TODO: ask for skill invoke
                act.oc_tag = True
                new_act = OpticalCloak(target=target, ori=act)
                return new_act
        return act

class UFOSkill(Skill):
    associated_action = None
    target = None

class GreenUFOSkill(UFOSkill):
    increment = 1

class RedUFOSkill(UFOSkill):
    increment = 1

@register_eh
class UFODistanceHandler(EventHandler):
    execute_before = (DistanceValidator,)
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, CalcDistance):
            source = act.source
            for s in source.skills:
                if issubclass(s, RedUFOSkill):
                    act.correction += s.increment

            dist = act.distance
            for p in dist.keys():
                for s in p.skills:
                    if issubclass(s, GreenUFOSkill):
                        dist[p] += s.increment
        return act

class WeaponSkill(Skill):
    range = 1

@register_eh
class WeaponDistanceHandler(EventHandler):
    execute_before = (DistanceValidator,)
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, CalcDistance):
            card = act.card
            if issubclass(card.associated_action, basic.BaseAttack):
                source = act.source
                for s in source.skills:
                    if issubclass(s, WeaponSkill):
                        act.correction += s.range - 1
        return act


class HakuroukenSkill(Skill):
    associated_action = None
    target = None
    range = 2

class Hakurouken(InternalAction):
    # 白楼剑
    def __init__(self, act):
        assert isinstance(act, basic.BaseAttack)
        self.action = act

    def apply_action(self):
        act = self.action
        target = act.target
        shield_skills = []
        skills = target.skills
        for i, s in reversed(list(enumerate(skills))):
            if issubclass(s, ShieldSkill):
                del skills[i]
                shield_skills.append(s)
        rst = Game.getgame().process_action(act)
        skills.extend(shield_skills)
        return rst

@register_eh
class HakuroukenEffectHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            if hasattr(act, 'hakurouken_tag'):
                return act
            act.hakurouken_tag = True
            source = act.source
            if source.has_skill(HakuroukenSkill):
                act = Hakurouken(act)
                return act
        return act
