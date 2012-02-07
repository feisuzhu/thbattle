# All Actions, EventHandlers are here
from game.autoenv import Game, EventHandler, Action, GameError

from network import Endpoint
import random
import types

import logging
log = logging.getLogger('SimpleGame_Actions')

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
        target = self.target
        if target.life < target.maxlife:
            target.life = min(target.life + self.amount, target.maxlife)
            return True
        else:
            return False

class DropCardIndex(GenericAction):

    def __init__(self, target, card_indices):
        self.target = target
        self.card_indices = card_indices

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        card_indices = self.card_indices
        ci_sorted = sorted(card_indices, reverse=True)

        cards = [target.cards[i] for i in card_indices]
        for i in ci_sorted:
            del target.cards[i]

        g.players.exclude(target).reveal(cards)

        self.cards = cards
        return True

class ChooseCard(GenericAction):

    def __init__(self, target, cond):
        self.target = target
        self.cond = cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        input = target.user_input('choose_card', self)

        if not (input and isinstance(input, list)):
            return False # default action

        n = len(input)
        if not n: return False

        if [i.__class__ for i in input] != [int]*n: # must be a list of ints
            return False

        input.sort()
        if input[0] < 0 or input[-1] >= len(target.cards): # index out of range
            return False

        cards = [target.cards[i] for i in input]
        g.players.exclude(target).reveal(cards)

        if self.cond(cards):
            self.card_indices = input
            return True
        else:
            return False

    def default_action(self):
        return False

class DropUsedCard(DropCardIndex): pass

class UseCard(GenericAction):
    def __init__(self, target, cond=None):
        self.target = target
        if cond:
            self.cond = cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        choose_action = ChooseCard(target, self.cond)
        if not g.process_action(choose_action):
            return False
        else:
            drop = DropUsedCard(target, card_indices=choose_action.card_indices)
            g.process_action(drop)
            return True

class UseGraze(UseCard):
    def cond(self, cl):
        return len(cl) == 1 and cl[0].type == 'graze'

class DropCardStage(GenericAction):

    def __init__(self, target):
        self.target = target

    def apply_action(self):
        target = self.target
        life = target.life
        n = len(target.cards) - life
        if n<=0:
            return True
        g = Game.getgame()
        choose_action = ChooseCard(target, cond = lambda cl: len(cl) == n)
        if g.process_action(choose_action):
            g.process_action(DropCardIndex(target, card_indices=choose_action.card_indices))
        else:
            g.process_action(DropCardIndex(target, card_indices=range(max(n, 0))))
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
    def __init__(self, source, target, card, card_index):
        # FIXME: this sucks, but ui requires it.
        # Can be fixed when Deck comes out.
        self.source, self.target, self.card, self.card_index= \
            source, target, card, card_index

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        action = card.assocated_action
        g.process_action(DropUsedCard(self.source, card_indices=[self.card_index]))
        if action:
            action = action(source=self.source, target=self.target)
            return g.process_action(action)
        return False

class ActionStage(GenericAction):

    def __init__(self, target):
        self.target = target

    def default_action(self):
       return True

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        while True:
            input = target.user_input('action_stage_usecard')
            if not input: break
            if type(input) != list: break

            card_index, object_index = input

            if type(card_index) != int or type(object_index) != int:
                break

            n = len(target.cards)
            if not 0 <= card_index < n:
                break

            if not 0 <= object_index < len(g.players):
                break

            card = target.cards[card_index]
            g.players.exclude(target).reveal(card)

            object = g.players[object_index]
            g.process_action(LaunchCard(target, object, card, card_index))

        return True
