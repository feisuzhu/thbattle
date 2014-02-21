# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import DrawCards, UserAction, LaunchCard, Pindian
from ..cards import Skill, t_None, t_OtherN, AttackCard, DuelCard, TreatAsSkill, BaseAttack
from ..inputlets import ChooseOptionInputlet
from weakref import WeakSet


class InciteAttack(TreatAsSkill):
    treat_as = AttackCard

    def check(self):
        return not self.associated_cards

class InciteFailAttack(InciteAttack):
    distance = 99999

class InciteAttackAction(LaunchCard):
    def __init__(self, source, target, inciter):
        LaunchCard.__init__(self, source, [target], InciteAttack(source))
        self.inciter = inciter

class InciteFailAttackAction(LaunchCard):
    def __init__(self, source, target, inciter):
        LaunchCard.__init__(self, source, [inciter], InciteFailAttack(source))
        self.victim = target

class InciteFailAction(UserAction):
    def __init__(self, source, target, inciter):
        self.source = source
        self.target = target
        self.inciter = inciter

    def apply_action(self):
        return True

class InciteAction(UserAction):
    def apply_action(self):
        src = self.source
        tags = src.tags
        tgt, victim = self.target_list
        
        tags['incite_tag'] = tags['turn_count']
        
        g = Game.getgame()
        if g.process_action(Pindian(src, tgt)):
            g.process_action(InciteAttackAction(tgt, victim, src))

        elif user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            g.process_action(InciteFailAttackAction(tgt, victim, src))

        else:
            g.process_action(InciteFailAction(tgt, victim, src))

        return True

    def is_valid(self):
        src = self.source
        tags = src.tags
        if tags['turn_count'] <= tags['incite_tag']:
            return False

        tgt, victim = self.target_list
        if not Pindian(src, tgt).can_fire(): return False
        return InciteAttackAction(tgt, victim, src).can_fire()


class Incite(Skill):
    associated_action = InciteAction

    def target(self, g, source, tl):
        if not tl or tl[0] is source:
            return ([], False)

        tl_, valid = AttackCard.target(g, tl[0], tl[1:])
        return tl[:1] + tl_, valid

    def check(self):
        return not self.associated_cards

class Reversal(Skill):
    associated_action = None 
    target = t_None

class ReversalDuel(TreatAsSkill):
    treat_as = DuelCard

    def check(self):
        return not self.associated_cards

class ReversalHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'before_launch_card':
            if not act.card.is_card(AttackCard):
                return act
        
            def nhand(p):
                return len(p.cards) + len(p.showncards)

            src = act.source
            g = Game.getgame()
            for tgt in act.target_list[:]:
                if tgt is g.current_turn: continue
                if not tgt.has_skill(Reversal): continue
                if not user_input([tgt], 
                    ChooseOptionInputlet(self, (False, True))
                ): continue
                
                g.process_action(DrawCards(tgt, 1))
                if nhand(tgt) > nhand(src):
                    tags = tgt.tags
                    tags.setdefault('reversed_act', WeakSet()).add(act.action)
                    g.process_action(LaunchCard(src, [tgt], ReversalDuel(src)))

        elif evt_type == 'action_before' and isinstance(act, BaseAttack):
            tgt = act.target
            if not tgt.has_skill(Reversal): return act

            pact = getattr(act, 'parent_action', act)
            if pact in tgt.tags.get('reversed_act', ()):
                act.cancelled = True

        return act

@register_character
class Seija(Character):
    skills = [Incite, Reversal]
    eventhandlers_required = [ReversalHandler]
    maxlife = 3
