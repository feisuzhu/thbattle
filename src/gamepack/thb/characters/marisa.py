# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *
from ..skill import *

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
                pass
                #pl.remove(tgt)
            except ValueError:
                pass

            pl = user_choose_players(self, tgt, pl, lambda l: len(l) <= 2)

            if not pl: return act

            for p in pl:
                c = random_choose_card([p.cards, p.showncards])
                if not c: continue
                tgt.reveal(c)
                migrate_cards([c], tgt.cards)
            act.cancelled = True

        return act


@register_character
class Marisa(Character):
    skills = [Borrow]
    eventhandlers_required = [BorrowHandler]
    maxlife = 4
