# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

from ..thbraid import use_faith


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
    execute_after = ('HakuroukenEffectHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            src = act.source
            if not src.has_skill(FateSpear): return act
            tgt = act.target

            while True:
                if tgt.life > src.life: break
                if len(tgt.cards) + len(tgt.showncards) < len(src.cards) + len(src.showncards): break
                return act

            if user_choose_option(self, act.source):
                Game.getgame().process_action(FateSpearAction(act))

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


class HeartBreakAction(InevitableAttack):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.amount = 2

    def apply_action(self):
        use_faith(self.target, 4)
        return InevitableAttack.apply_action(self)


class HeartBreak(Skill):
    associated_action = HeartBreakAction
    target = t_OtherOne

    @property
    def color(self):
        return Card.RED

    def is_card(self, cls):
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 4


class NeverNightAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        for p in self.target_list:
            if not (p.cards or p.showncards or p.equips):
                if p.faiths:
                    g.process_action(DropCards(p, p.faiths))
            else:
                cats = [p.cards, p.showncards, p.equips]
                c = choose_peer_card(tgt, p, cats)
                if not c:
                    c = random_choose_card(cats)

                g.process_action(DropCards(p, [c]))

        return True


class NeverNight(Skill):
    associated_action = NeverNightAction
    target = t_All

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 4


class ScarletFogAction(UserAction):
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa

class ScarletFog(Skill):

class RemiliaEx2(Character):
    maxlife = 6
    maxfaith = 4
    skills = [HeartBreak, NeverNight, VampireKiss, FateSpear, ScarletFog]
    eventhandlers_required = [FateSpearHandler, VampireKissHandler]

    initial_equips = [(GungnirCard, SPADE, Q)]


@register_ex_character
class RemiliaEx(Character):
    maxlife = 6
    maxfaith = 4
    skills = [HeartBreak, NeverNight, VampireKiss]
    eventhandlers_required = [VampireKissHandler]

    initial_equips = [(GungnirCard, SPADE, Q)]
    stage2 = RemiliaEx2
