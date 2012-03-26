# -*- coding: utf-8 -*-

from .base import *
from ..skill import *
from ..actions import *

from . import basic, spellcard, base

from utils import check, CheckFailed

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
                    try:
                        _from.owner.skills.remove(c.equipment_skill)
                    except ValueError:
                        pass

            if to.type == CardList.EQUIPS:
                for c in cards:
                    to.owner.skills.append(c.equipment_skill)

        return args

class ShieldSkill(Skill):
    associated_action = None
    target = t_None

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
                if target.user_input('choose_option', self):
                    act.oc_tag = True
                    new_act = OpticalCloak(target=target, ori=act)
                    return new_act
        return act

class UFOSkill(Skill):
    associated_action = None
    target = t_None

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

class HakuroukenSkill(WeaponSkill):
    associated_action = None
    target = t_None
    range = 2

class Hakurouken(InternalAction):
    # 白楼剑
    def __init__(self, act):
        assert isinstance(act, basic.BaseAttack)
        self.action = act

    def apply_action(self):
        act = self.action
        target = act.target
        skills = target.skills
        for e in target.equips:
            s = e.equipment_skill
            if issubclass(s, ShieldSkill):
                skills.remove(s)
        rst = Game.getgame().process_action(act)
        for card in target.equips:
            s = card.equipment_skill
            if issubclass(s, ShieldSkill):
                skills.append(s)
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

class ElementalReactorSkill(WeaponSkill):
    associated_action = None
    target = t_None
    range = 1

@register_eh
class ElementalReactorHandler(EventHandler):
    # 八卦炉
    def handle(self, evt_type, act):
        if evt_type == 'action_stage_action':
            actor = act.actor
            if actor.has_skill(ElementalReactorSkill):
                if not actor.tags.get('reactor_tag', False):
                    actor.tags['reactor_tag'] = True
                    actor.tags['attack_num'] += 1000
            else:
                if actor.tags.get('reactor_tag', False):
                    actor.tags['reactor_tag'] = False
                    actor.tags['attack_num'] -= 1000
        elif evt_type == 'action_after' and isinstance(act, ActionStage):
            act.actor.tags['reactor_tag'] = False

        return act

class UmbrellaSkill(ShieldSkill):
    pass

@register_eh
class UmbrellaHandler(EventHandler):
    # 紫的阳伞
    execute_before = (spellcard.RejectHandler, )
    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, (spellcard.MapCannon, spellcard.WorshipersCarnival)):
                if act.target.has_skill(UmbrellaSkill):
                    act.cancelled = True
        return act

class RoukankenSkill(WeaponSkill):
    range = 3
    associated_action = None
    target = t_None

@register_eh
class RoukankenHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, basic.BaseAttack):
            src, tgt = act.source, act.target
            if src.has_skill(RoukankenSkill) and not act.succeeded:
                if src.user_input('choose_option', self):
                    g = Game.getgame()
                    a = basic.UseAttack(target=src)
                    if g.process_action(a):
                        card = a.associated_cards[0]
                        a = basic.Attack(source=src, target=tgt)
                        a.associated_card = card
                        g.process_action(a)
        return act

class GungnirSkill(TreatAsSkill, WeaponSkill):
    treat_as = Card.card_classes['AttackCard'] # arghhhhh, nasty circular references!
    range = 3
    target = t_OtherOne
    def check(self):
        cl = self.associated_cards
        cat = (base.CardList.HANDCARD, base.CardList.SHOWNCARD)
        if not all(c.resides_in.type in cat for c in cl): return False
        return len(cl) == 2

class LaevateinSkill(TreatAsSkill, WeaponSkill):
    treat_as = Card.card_classes['AttackCard'] # arghhhh, the same reason ^
    range = 4
    target = t_OtherLessThanN(3)
    def check(self):
        try:
            cl = self.associated_cards
            check(len(cl) == 1)
            card = cl[0]
            from .definition import AttackCard
            check(isinstance(card, AttackCard))
            actor = card.resides_in.owner
            check(len(actor.cards) + len(actor.shown_cards) == 1)
            return True
        except CheckFailed:
            return False
