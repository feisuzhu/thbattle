# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Borrow(Skill):
    associated_action = None
    target = t_None

class BorrowAction(GenericAction):
    def __init__(self, source, target_list):
        self.source = source
        self.target_list = target_list

    def apply_action(self):
        src = self.source
        for p in self.target_list:
            c = random_choose_card([p.cards, p.showncards])
            if not c: continue
            Game.getgame().players.exclude(p).reveal(c)
            migrate_cards([c], src.showncards)

        return True


class BorrowHandler(EventHandler):
    execute_after = ('FrozenFrogHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if tgt.dead: return act
            if not tgt.has_skill(Borrow): return act
            if not user_choose_option(self, tgt): return act

            g = Game.getgame()
            pl = [p for p in g.players if not p.dead and (p.cards or p.showncards)]
            try:
                pl.remove(tgt)
            except ValueError:
                pass

            pl = user_choose_players(self, tgt, pl)

            if not pl: return act
            g.process_action(BorrowAction(tgt, pl))
            act.cancelled = True

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[:2], True)

class MasterSpark(Skill):
    associated_action = Attack
    target = t_OtherOne

    def check(self):
        cl = self.associated_cards
        if cl and len(cl) == 2 and all(
            c.is_card(GrazeCard)
            for c in cl
        ): return True

        return False

    def is_card(self, cls):
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)


@register_character
class Marisa(Character):
    skills = [Borrow, MasterSpark]
    eventhandlers_required = [BorrowHandler]
    maxlife = 4
