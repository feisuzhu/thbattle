# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, user_input
from ..actions import UserAction, DrawCards, Damage, Fatetell
from ..actions import ask_for_action, migrate_cards
from ..cards import Skill, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character


class Masochist(Skill):
    associated_action = None
    target = t_None


class MasochistAction(UserAction):
    no_reveal = True

    def __init__(self, target, n):
        self.source, self.target, self.amount = target, target, n

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        a = DrawCards(tgt, self.amount * 2)
        g.process_action(a)
        self.cards = cards = a.cards
        n = len(cards)
        while n > 0:
            pl = [p for p in g.players if not p.dead]
            pl.remove(tgt)
            _, rst = ask_for_action(self, [tgt], ('cards',), pl)
            if not rst: return True
            cl, pl = rst
            pl[0].reveal(cl)
            migrate_cards(cl, pl[0].cards)
            n -= len(cl)

        return True

    usage = 'handover'
    def cond(self, cl):
        cards = self.cards
        return all(c in cards for c in cl)

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class MasochistHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if tgt.dead: return act
            if not tgt.has_skill(Masochist): return act
            if not act.amount: return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(MasochistAction(tgt, act.amount))

        return act


class Hermit(Skill):
    associated_action = None
    target = t_None


class HermitHandler(EventHandler):
    execute_before = ('YinYangOrbHandler', )
    execute_after = ('TrialHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Fatetell):
            tgt = act.target
            if not tgt.has_skill(Hermit): return act
            migrate_cards([act.card], tgt.cards)

        return act


@register_character
class Tenshi(Character):
    skills = [Masochist, Hermit]
    eventhandlers_required = [MasochistHandler, HermitHandler]
    maxlife = 3
