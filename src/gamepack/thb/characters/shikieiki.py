# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Trial(Skill):
    associated_action = None
    target = t_None

class Majesty(Skill):
    associated_action = None
    target = t_None

class TrialAction(GenericAction):
    def __init__(self, source, target, ft, card):
        self.source, self.target, self.ft, self.card = \
            source, target, ft, card

    def apply_action(self):
        g = Game.getgame()
        c = self.card
        g.players.exclude(self.source).reveal(c)
        g.process_action(DropCards(self.source, [c]))
        self.ft.card = c
        return True

class TrialHandler(EventHandler):
    execute_before = ('YinYangOrbHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Fatetell):
            g = Game.getgame()
            pl = g.players.rotate_to(act.target)
            for p in pl:
                if p.dead: continue
                if not p.has_skill(Trial): continue

                if not user_choose_option(self, p): return act

                cats = [p.cards, p.showncards, p.equips]
                cards = user_choose_cards(self, p, cats)
                if cards:
                    c = cards[0]
                    g.process_action(TrialAction(p, act.target, act, c))

        return act

    def cond(self, cards):
        return len(cards) == 1

class MajestyAction(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        cats = [
            tgt.cards, tgt.showncards, tgt.equips
        ]
        c = choose_peer_card(src, tgt, cats)
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

        if not user_choose_option(self, tgt): return act

        Game.getgame().process_action(MajestyAction(tgt, src))

        return act

@register_character
class Shikieiki(Character):
    skills = [Trial, Majesty]
    eventhandlers_required = [TrialHandler, MajestyHandler]
    maxlife = 3
