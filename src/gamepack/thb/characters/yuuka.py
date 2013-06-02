# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import register_character, Character
from ..actions import BaseDamage, GenericAction, TryRevive
from ..cards import Attack, AttackCard, Card, GrazeCard, Skill, t_None, t_OtherOne
from utils import classmix


class FlowerQueen(Skill):
    associated_action = Attack
    target = t_OtherOne
    distance = 1

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1: return False
        c = cl[0]
        if not c.suit == Card.CLUB: return False
        return c.resides_in and c.resides_in.type in (
            'cards', 'showncards', 'equips',
        )

    def is_card(self, cls):
        if issubclass(AttackCard, cls) or issubclass(GrazeCard, cls): return True
        return isinstance(self, cls)


class MagicCannon(Skill):
    associated_action = None
    target = t_None


class PerfectKill(Skill):
    associated_action = None
    target = t_None
    distance = 1


class MagicCannonAttack(Attack):
    pass


class PerfectKillAction(GenericAction):
    def __init__(self, source, target, act):
        self.source, self.target, self.act = \
            source, target, act

    def apply_action(self):
        self.act.asklist = [self.source, self.target]
        return True


class YuukaHandler(EventHandler):
    execute_before = ('ScarletRhapsodySwordHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Attack):
            c = getattr(act, 'associated_card', None)
            if not c: return act
            src = act.source
            if not src.has_skill(MagicCannon): return act
            if c.color == Card.RED:
                act.damage += 1
                act.__class__ = classmix(MagicCannonAttack, act.__class__)

        elif evt_type == 'action_before' and isinstance(act, TryRevive):
            g = Game.getgame()
            dmg = act.dmgact
            assert isinstance(dmg, BaseDamage)
            src = dmg.source
            tgt = dmg.target
            if src != tgt and src and src.has_skill(PerfectKill):
                g.process_action(PerfectKillAction(src, dmg.target, act))

        return act


@register_character
class Yuuka(Character):
    skills = [FlowerQueen, MagicCannon, PerfectKill]
    eventhandlers_required = [YuukaHandler]
    maxlife = 3
