# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character_to
from ..actions import UserAction, ActionStage, ShowCards, DropCards
from ..actions import migrate_cards, user_choose_cards
from ..cards import Card, Skill, t_None, t_OtherOne
from ..inputlets import ChooseOptionInputlet, HopeMaskInputlet


class HopeMaskAction(UserAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        n = 1 + tgt.maxlife - tgt.life
        cards = g.deck.getcards(n)

        tgt.reveal(cards)
        putback, acquire = user_input([tgt], HopeMaskInputlet(self, cards), timeout=20)
        acquire and g.process_action(ShowCards(tgt, acquire))
        migrate_cards(acquire, tgt.cards)

        assert not putback or set(putback) == set(g.deck.getcards(len(putback)))

        deck = g.deck.cards
        for i, c in enumerate(putback):
            deck[i] = c

        assert not putback or putback == g.deck.getcards(len(putback))

        self.acquire = acquire

        return True


class HopeMaskHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            tgt = act.target
            if not tgt.has_skill(HopeMask): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act
            Game.getgame().process_action(HopeMaskAction(tgt, tgt))

        return act


class HopeMask(Skill):
    associated_action = None
    target = t_None


class DarkNohAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        src.tags['darknoh_tag'] = src.tags['turn_count']
        sk = self.associated_card
        card = sk.associated_cards[0]
        self.card = card
        migrate_cards([sk], tgt.showncards, unwrap=True)
        self.n = n = len(tgt.cards) + len(tgt.showncards) - tgt.life
        if n <= 0: return True

        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        if not cards:
            cl = list(tgt.cards) + list(tgt.showncards)
            try:
                cl.remove(card)
            except:
                pass

            cards = cl[:n]

        g.players.reveal(cards)
        g.process_action(DropCards(tgt, cards))

        return True

    def cond(self, cards):
        if len(cards) != self.n or self.card in cards:
            return False

        tgt = self.target
        if not all([c in tgt.cards or c in tgt.showncards for c in cards]):
            return False

        return True

    def is_valid(self):
        src = self.source
        tgt = self.target

        if src.tags['darknoh_tag'] >= src.tags['turn_count']:
            return False

        if src.life > tgt.life:
            return False

        return True


class DarkNoh(Skill):
    no_drop = True
    associated_action = DarkNohAction
    target = t_OtherOne

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if c.resides_in is None: return False
        if not c.resides_in.type in ('cards', 'showncards', 'equips'): return False
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        return True


@register_character_to(('-raid', ))
class Kokoro(Character):
    skills = [HopeMask, DarkNoh]
    eventhandlers_required = [HopeMaskHandler]
    maxlife = 3
