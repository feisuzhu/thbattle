# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Borrow(Skill):
    associated_action = None
    target = t_None

class BorrowHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if not tgt.has_skill(Borrow): return act
            if not tgt.user_input('choose_option', self): return act

            g = Game.getgame()
            pl = [p for p in g.players if not p.dead and (p.cards or p.showncards)]
            try:
                pl.remove(tgt)
            except ValueError:
                pass

            pl = user_choose_players(self, tgt, pl)

            if not pl: return act

            for p in pl:
                c = random_choose_card([p.cards, p.showncards])
                if not c: continue
                tgt.reveal(c)
                migrate_cards([c], tgt.cards)
            act.cancelled = True

        return act

    def target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[:2], True)

@register_character
class Marisa(Character):
    skills = [Borrow]
    eventhandlers_required = [BorrowHandler]
    maxlife = 4
