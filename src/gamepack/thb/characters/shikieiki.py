# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, DropCards, Damage, UseCardAction
from ..actions import migrate_cards, ask_for_action
from ..cards import Skill, t_None, VirtualCard
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


class Trial(Skill):
    associated_action = None
    target = t_None


class Majesty(Skill):
    associated_action = None
    target = t_None


class TrialAction(UserAction):
    def __init__(self, source, target, ft, card):
        self.source, self.target, self.ft, self.card = \
            source, target, ft, card

    def apply_action(self):
        g = Game.getgame()
        c = self.card
        g.players.exclude(self.source).reveal(c)
        g.process_action(UseCardAction(self.source, [c]))
        self.ft.set_card(c)
        return True

    def is_valid(self):
        return UseCardAction(self.source, [self.card]).can_fire()


class TrialHandler(EventHandler):
    execute_before = ('YinYangOrbHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'fatetell':
            g = Game.getgame()
            pl = g.players.rotate_to(act.target)
            for p in pl:
                if p.dead: continue
                if not p.has_skill(Trial): continue

                if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                    return act

                action = lambda p, cl, pl: TrialAction(p, act.target, act, cl[0])

                action = ask_for_action(self, action, [p], ('cards', 'showncards', 'equips'), [])
                if action:
                    g.process_action(action)

        return act

    def cond(self, cards):
        return len(cards) == 1 and not isinstance(cards[0], VirtualCard)


class MajestyAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards', 'equips')))
        if not c: return False
        src.reveal(c)
        migrate_cards([c], src.cards)
        return True


class MajestyHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, Damage): return act
        src, tgt = act.source, act.target
        if not src: return act

        cats = [
            src.cards, src.showncards, src.equips
        ]

        if not any(cats): return act
        if tgt.dead: return act
        if not tgt.has_skill(Majesty): return act

        if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        Game.getgame().process_action(MajestyAction(tgt, src))

        return act


@register_character
class Shikieiki(Character):
    skills = [Trial, Majesty]
    eventhandlers_required = [TrialHandler, MajestyHandler]
    maxlife = 3
