# All Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, SyncPrimitive

from network import Endpoint
import random

import logging
log = logging.getLogger('SimpleGame_Actions')

# ------------------------------------------
# aux functions
def user_choose_card(act, target, cond):
    from utils import check, CheckFailed
    g = Game.getgame()
    input = target.user_input('choose_card', act) # list of card ids

    try:
        check(input and isinstance(input, list))

        n = len(input)
        check(n)

        check(all(i.__class__ == int for i in input)) # must be a list of ints

        cards = g.deck.getcards(input)
        cs = set(cards)

        check(len(cs) == n) # repeated ids

        check(cs.issubset(set(target.cards))) # Whose cards?! Wrong ids?!

        g.players.exclude(target).reveal(cards)

        check(cond(cards))

        return cards
    except CheckFailed:
        return None

def random_choose_card(target):
    c = random.choice(target.cards)
    v = SyncPrimitive(c.syncid)
    g = Game.getgame()
    g.players.reveal(v)
    v = v.value
    cl = [c for c in target.cards if c.syncid == v]
    assert len(cl) == 1
    return cl[0]

action_eventhandlers = set()
def register_eh(cls):
    action_eventhandlers.add(cls)
    return cls

# ------------------------------------------

class GenericAction(Action): pass # others

class UserAction(Action): pass # card/character skill actions
class BaseAction(UserAction): pass # attack, graze, heal
class SpellCardAction(UserAction): pass

class InternalAction(Action): pass # actions for internal use, should not be intercepted by EHs


class Damage(GenericAction):

    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        target = self.target
        target.life -= self.amount
        if target.life <= 0:
            Game.getgame().emit_event('player_dead', target)
            target.dead = True
        return True

class Attack(BaseAction):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = UseGraze(target)
        if not g.process_action(graze_action):
            g.process_action(Damage(source, target, amount=self.damage))
            return True
        else:
            return False

class Heal(BaseAction):

    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        source = self.source # target is ignored
        if source.life < source.maxlife:
            source.life = min(source.life + self.amount, source.maxlife)
            return True
        else:
            return False

class Demolition(SpellCardAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if not len(target.cards): return False

        card = random_choose_card(target)
        self.card = card
        g.players.exclude(target).reveal(card)
        g.process_action(
            DropCards(target=target, cards=[card])
        )
        return True

class Reject(SpellCardAction):
    def __init__(self, source, target_act):
        self.source = source
        self.target_act = target_act

    def apply_action(self):
        if not isinstance(self.target_act, SpellCardAction):
            return False
        self.target_act.cancelled = True
        return True

@register_eh
class RejectHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction):
            g = Game.getgame()

            p, cid_list = g.players.user_input_any(
                'choose_card', self._expects, self
            )

            if p:
                card, = g.deck.getcards(cid_list) # card was already revealed
                action = Reject(source=p, target_act=act)
                action.associated_card = card
                g.process_action(DropUsedCard(p, [card]))
                g.process_action(action)
        return act

    def _expects(self, p, cid_list):
        from utils import check, CheckFailed
        try:
            check(isinstance(cid_list, list))
            check(len(cid_list) == 1)
            check(isinstance(cid_list[0], int))

            g = Game.getgame()
            card, = g.deck.getcards(cid_list)
            check(card in p.cards)

            g.players.exclude(p).reveal(card)

            check(self.cond([card]))
            return True
        except CheckFailed:
            return False

    def cond(self, cardlist):
        from utils import check, CheckFailed
        import cards
        try:
            check(len(cardlist) == 1)
            check(isinstance(cardlist[0], cards.RejectCard))
            return True
        except CheckFailed:
            return False

# ---------------------------------------------------



class DropCards(GenericAction):

    def __init__(self, target, cards):
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = self.cards

        tcs = set(target.cards)
        cs = set(cards)
        assert cs.issubset(tcs), 'WTF?!'
        target.cards = list(tcs - cs)

        return True

class DropUsedCard(DropCards): pass

class UseCard(GenericAction):
    def __init__(self, target):
        self.target = target
        # self.cond = __subclass__.cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        cards = user_choose_card(self, target, self.cond)
        if not cards:
            return False
        else:
            drop = DropUsedCard(target, cards=cards)
            g.process_action(drop)
            return True

class UseGraze(UseCard):
    def cond(self, cl):
        import cards
        return len(cl) == 1 and isinstance(cl[0], cards.GrazeCard)

class DropCardStage(GenericAction):

    def cond(self, cards):
        t = self.target
        return len(cards) == len(t.cards) - t.life

    def __init__(self, target):
        self.target = target

    def apply_action(self):
        target = self.target
        life = target.life
        n = len(target.cards) - life
        if n<=0:
            return True
        g = Game.getgame()
        cards = user_choose_card(self, target, cond=self.cond)
        if cards:
            g.process_action(DropCards(target, cards=cards))
        else:
            cards = target.cards[:max(n, 0)]
            g.players.exclude(target).reveal(cards)
            g.process_action(DropCards(target, cards=cards))
        return True

class DrawCards(GenericAction):

    def __init__(self, target, amount=2):
        self.target = target
        self.amount = amount

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = g.deck.drawcards(self.amount)

        target.reveal(cards)
        target.cards.extend(cards)
        self.cards = cards
        return True

class DrawCardStage(DrawCards): pass

class LaunchCard(GenericAction):
    def __init__(self, source, target_list, card):
        self.source, self.target_list, self.card = source, target_list, card

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        action = card.associated_action
        g.process_action(DropUsedCard(self.source, cards=[card]))
        if action:
            t = card.target
            if t == 'self':
                target_list = [self.source]
            elif isinstance(t, int):
                target_list = self.target_list
                if len(target_list) != t: return False

            for target in target_list:
                a = action(source=self.source, target=target)
                a.associated_card = card
                g.process_action(a)
            return True
        return False

class ActionStage(GenericAction):

    def __init__(self, target):
        self.actor = target

    def default_action(self):
       return True

    def apply_action(self):
        g = Game.getgame()
        actor = self.actor

        while True:
            input = actor.user_input('action_stage_usecard')
            if not input: break
            if type(input) != list: break

            card_id, target_list = input

            if type(card_id) != int or type(target_list) != list:
                break

            card, = g.deck.getcards([card_id])
            if not card: break
            if not card in actor.cards: break

            target_list = [g.player_fromid(i) for i in target_list]
            from game import AbstractPlayer
            if not all(isinstance(p, AbstractPlayer) for p in target_list):
                break

            g.players.exclude(actor).reveal(card)

            g.process_action(LaunchCard(actor, target_list, card))

        return True
