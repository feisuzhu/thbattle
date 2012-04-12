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

class TrialHandler(EventHandler):
    execute_before = (YinYangOrbHandler, )
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Fatetell):
            g = Game.getgame()
            pl = g.players.rotate_to(act.target)
            for p in pl:
                if p.dead: continue
                if not p.has_skill(Trial): continue

                if not p.user_input('choose_option', self): return act

                cats = [p.cards, p.showncards, p.equips]
                cards = user_choose_cards(self, p, cats)
                if cards:
                    c = cards[0]
                    g.players.exclude(p).reveal(c)
                    migrate_cards(cards, g.deck.droppedcards)
                    act.card = c
        return act

    def cond(self, cards):
        return len(cards) == 1

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

        if not tgt.user_input('choose_option', self): return act

        c = choose_peer_card(tgt, src, cats)
        if not c: return act
        tgt.reveal(c)
        migrate_cards([c], tgt.cards)
        return act

@register_character
class Shikieiki(Character):
    skills = [Trial, Majesty]
    eventhandlers_required = [TrialHandler, MajestyHandler]
    maxlife = 3
