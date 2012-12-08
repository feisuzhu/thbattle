# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *
from itertools import chain


class DrawingLotAction(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        tags = src.tags
        tags['drawinglot_tag'] = tags['turn_count']

        g  = Game.getgame()
        diff = max(p.life for p in g.players) - tgt.life
        diff = min(diff, 4)
        diff = max(diff, 1)

        g.process_action(DrawCards(tgt, amount=diff))
        self.amount = diff
        return True

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['drawinglot_tag']


class DrawingLot(Skill):
    associated_action = DrawingLotAction
    target = t_One

    def check(self):
        if self.associated_cards: return False
        return True


class Miracle(Skill):
    associated_action = None
    target = t_None


class MiracleAction(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        amount = min(src.maxlife - src.life, 4)
        self.amount = amount
        g = Game.getgame()
        g.process_action(DrawCards(tgt, amount))
        return True


class MiracleHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if not tgt.has_skill(Miracle): return act
            if tgt.dead: return act
            g = Game.getgame()
            
            candidates = [p for p in g.players if p.life < p.maxlife and not p.dead]
            if not candidates: return act
            pl = user_choose_players(self, tgt, candidates)
            if not pl: return act
            g = Game.getgame()
            g.process_action(MiracleAction(tgt, pl[0]))

        return act

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)


@register_character
class Sanae(Character):
    skills = [DrawingLot, Miracle]
    eventhandlers_required = [MiracleHandler]
    maxlife = 3
