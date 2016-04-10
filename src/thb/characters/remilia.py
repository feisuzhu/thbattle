# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import Damage, GenericAction
from thb.cards import Attack, AttackCard, Card, Heal, InevitableAttack, Skill, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class SpearTheGungnir(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
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
    interested = ('action_before',)
    execute_before = ('ScarletRhapsodySwordHandler', )
    execute_after = (
        'HakuroukenEffectHandler',
        'HouraiJewelHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Attack):
            src = act.source
            if not src.has_skill(SpearTheGungnir): return act
            if isinstance(act, InevitableAttack): return act

            tgt = act.target

            while True:
                if tgt.life > src.life: break
                if len(tgt.cards) + len(tgt.showncards) < len(src.cards) + len(src.showncards): break
                return act

            if user_input([act.source], ChooseOptionInputlet(self, (False, True))):
                Game.getgame().process_action(SpearTheGungnirAction(act))

        return act


class VampireKiss(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class VampireKissAction(GenericAction):
    def apply_action(self):
        return Game.getgame().process_action(
            Heal(self.target, self.source)
        )


class VampireKissHandler(EventHandler):
    interested = ('action_apply', 'calcdistance')

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

        elif evt_type == 'calcdistance':
            src, card, dist = act

            if not card.is_card(AttackCard): return act
            if not src.has_skill(VampireKiss): return act
            if card.color != Card.RED: return act

            for p in dist:
                dist[p] -= 99999

        return act


@register_character_to('common')
class Remilia(Character):
    skills = [SpearTheGungnir, VampireKiss]
    eventhandlers_required = [SpearTheGungnirHandler, VampireKissHandler]
    maxlife = 4
