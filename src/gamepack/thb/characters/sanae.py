# -*- coding: utf-8 -*-

from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import Damage, DrawCards, ActiveDropCards, GenericAction, UserAction, user_choose_players, ask_for_drop
from ..cards import Skill, t_None, t_OtherOne, Attack
from ..inputlets import ChooseOptionInputlet


class DrawingLotAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        tags = src.tags
        tags['drawinglot_tag'] = tags['turn_count']

        g = Game.getgame()
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
    target = t_OtherOne

    def check(self):
        if self.associated_cards: return False
        return True


class Miracle(Skill):
    associated_action = None
    target = t_None


class MiracleAction(GenericAction):
    amount = -1

    def apply_action(self):
        tgt = self.target
        amount = tgt.maxlife - tgt.life
        self.amount = amount
        self._do_effect(tgt)

        g = Game.getgame()
        minlife = min([p.life for p in g.players if not p.dead])
        if not tgt.life == minlife: return True

        candidates = [p for p in g.players if p is not tgt and not p.dead]
        pl = user_choose_players(self, tgt, candidates)
        if not pl: return True

        self._do_effect(pl[0])
        return True

    def _do_effect(self, p):
        g = Game.getgame()
        amount = self.amount
        allcards = list(p.showncards) + list(p.cards) + list(p.equips)
        if len(allcards) <= amount:
            cards = allcards
        else:
            drop = ask_for_drop(self, p, ('cards', 'showncards', 'equips'))
            cards = drop.cards if drop else allcards[:amount]

        g.players.reveal(cards)

        g.process_action(ActiveDropCards(p, cards))
        g.process_action(DrawCards(p, amount))

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)

    def cond(self, cl):
        if len(cl) != self.amount: return False
        if any(['skill' in c.category for c in cl]): return False
        return True


class MiracleHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if not tgt.has_skill(Miracle): return act
            if tgt.dead: return act

            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            g.process_action(MiracleAction(tgt, tgt))

        return act


@register_character
class Sanae(Character):
    skills = [DrawingLot, Miracle]
    eventhandlers_required = [MiracleHandler]
    maxlife = 3
