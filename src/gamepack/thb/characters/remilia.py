# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class FateSpear(Skill):
    associated_action = None
    target = t_None

class FateSpearAction(GenericAction):
    def __init__(self, act):
        self.act = act
        self.source = act.source
        self.target = act.target

    def apply_action(self):
        self.act.__class__ = InevitableAttack
        return True

class FateSpearHandler(EventHandler):
    execute_before = ('DistanceValidator', )
    execute_after = ('AttackCardHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, CalcDistance):
            if not act.source.has_skill(FateSpear): return act
            g = Game.getgame()
            card = act.card
            if self.cardcond(card):
                act.force_valid()
        elif evt_type == 'action_before' and isinstance(act, Attack):
            if not act.source.has_skill(FateSpear): return act
            card = getattr(act, 'associated_card', None)
            if card and self.cardcond(card):
                Game.getgame().process_action(FateSpearAction(act))
        return act

    def cardcond(self, card):
        return card.is_card(GungnirSkill) or (
            card.is_card(AttackCard) and card.color == Card.RED
        )

class VampireKiss(Skill):
    distance = 2
    associated_action = None
    target = t_None

class VampireKissAction(GenericAction):
    def apply_action(self):
        return Game.getgame().process_action(
            Heal(self.target, self.source)
        )

class VampireKissHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not (src and src.has_skill(VampireKiss)): return act
            if src.life >= src.maxlife: return act
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            #cd = CalcDistance(src, VampireKiss(src))
            #g.process_action(cd)
            #rst = cd.validate()
            #if rst[act.target]:
            card = pact.associated_card
            if (not card) or card.color != Card.RED: return act
            g.process_action(VampireKissAction(src, tgt))

        return act

@register_character
class Remilia(Character):
    skills = [FateSpear, VampireKiss]
    eventhandlers_required = [FateSpearHandler, VampireKissHandler]
    maxlife = 4
