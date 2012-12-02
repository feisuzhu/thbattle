# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *
from itertools import chain


class DrawingLotAction(GenericAction):
    def apply_action(self):
        src = self.source
        tl = self.target_list
        tags = src.tags
        tags['drawinglot_tag'] = tags['turn_count']
        assert len(tl) == 2
        assert tl[0].life != tl[1].life
        a, b = tl
        if a.life > b.life:
            a, b = b, a

        self.lesser, self.greater = a, b

        diff = b.life - a.life
        self.diff = diff
        g  = Game.getgame()

        is_drawcard = src.user_input('choose_option', self)
        self.is_drawcard = False
        if is_drawcard:
            self.is_drawcard = True
            g.process_action(DrawCards(a, amount=diff))
        else:
            cats = [b.showncards, b.cards, b.equips]
            n = sum([len(l) for l in cats])
            
            cards = None
            if n > diff:
                cards = user_choose_cards(self, b, cats)

            if not cards:
                cards = list(chain.from_iterable(cats))[:diff]
                if cards:
                    g.players.exclude(b).reveal(cards) 

            if cards:
                g.process_action(DropCards(b, cards))

            self.amount = len(cards)
        return True

    def cond(self, cl):
        return len(cl) == self.diff

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['drawinglot_tag']


class DrawingLot(Skill):
    associated_action = DrawingLotAction

    @staticmethod
    def target(g, source, tl):
        tl = [t for t in tl if not t.dead]
        return (tl[:2], len(tl) >= 2 and tl[0].life != tl[1].life)

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
        amount = min(tgt.maxlife - tgt.life, 4)
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
            for _ in xrange(act.amount):
                candidates = [p for p in g.players if p.life < p.maxlife and not p.dead]
                if not candidates: return act
                pl = user_choose_players(self, tgt, candidates)
                if not pl: return act
                g = Game.getgame()
                g.process_action(MiracleAction(tgt, pl[0]))

        return act

    def choose_player_target(self, pl):
        return (pl[:1], len(pl) >= 1)

@register_character
class Sanae(Character):
    skills = [DrawingLot, Miracle]
    eventhandlers_required = [MiracleHandler]
    maxlife = 3
