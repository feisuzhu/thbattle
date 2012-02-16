# All Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError

from network import Endpoint
import random
import types

import logging
log = logging.getLogger('SimpleGame_Actions')

# ------------------------------------------
# aux functions
def choose_card(act, target, cond):
    g = Game.getgame()
    input = target.user_input('choose_card', act) # list of card ids

    if not (input and isinstance(input, list)):
        return None

    n = len(input)
    if not n: return None

    if any(i.__class__ != int for i in input): # must be a list of ints
        return None

    cards = g.deck.getcards(input)
    cs = set(cards)

    if len(cs) != n: # repeated ids
        return None

    if not cs.issubset(set(target.cards)): # Whose cards?! Wrong ids?!
        return None

    g.players.exclude(target).reveal(cards)

    if cond(cards):
        return cards
    else:
        return None
# ------------------------------------------

class GenericAction(Action): pass # others

class UserAction(Action): pass # card/character skill actions
class BaseAction(UserAction): pass # attack, graze, heal

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
        cards = choose_card(self, target, self.cond)
        if not cards:
            return False
        else:
            drop = DropUsedCard(target, cards=cards)
            g.process_action(drop)
            return True

class UseGraze(UseCard):
    def cond(self, cl):
        return len(cl) == 1 and cl[0].type == 'graze'

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
        cards = choose_card(self, target, cond=self.cond)
        if cards:
            g.process_action(DropCards(target, cards=cards))
        else:
            g.process_action(DropCards(target, cards=target.cards[:max(n, 0)]))
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
            for target in self.target_list:
                a = action(source=self.source, target=target)
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
