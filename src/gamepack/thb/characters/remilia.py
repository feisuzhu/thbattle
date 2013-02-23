# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *


class SpearTheGungnir(Skill):
    associated_action = None
    target = t_None


class SpearTheGungnirAction(GenericAction):
    def __init__(self, act):
        self.act = act
        self.source = act.source
        self.target = act.target

    def apply_action(self):
        self.act.__class__ = InevitableAttack
        return True


class SpearTheGungnirHandler(EventHandler):
    execute_after = ('HakuroukenEffectHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            src = act.source
            if not src.has_skill(SpearTheGungnir): return act
            tgt = act.target

            while True:
                if tgt.life > src.life: break
                if len(tgt.cards) + len(tgt.showncards) < len(src.cards) + len(src.showncards): break
                return act

            if user_choose_option(self, act.source):
                Game.getgame().process_action(SpearTheGungnirAction(act))

        return act


class VampireKiss(Skill):
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
            card = pact.associated_card
            if (not card) or card.color != Card.RED: return act
            g.process_action(VampireKissAction(src, tgt))

        return act


@register_character
class Remilia(Character):
    skills = [SpearTheGungnir, VampireKiss]
    eventhandlers_required = [SpearTheGungnirHandler, VampireKissHandler]
    maxlife = 4
