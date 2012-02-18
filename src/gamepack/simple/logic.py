from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList
from actions import *
from itertools import cycle
import random

import logging
log = logging.getLogger('SimpleGame')

class SimpleGame(Game):
    name = 'Simple Game'
    n_persons = 2

    if Game.CLIENT_SIDE:
        # not loading these things on server
        # FIXME: should it be here?
        from ui import SimpleGameUI as ui_class

    def game_start(self):
        # game started, init state
        from cards import Card, Deck

        for cls in action_eventhandlers:
            self.event_handlers.append(cls())

        for p in self.players:
            p.cards = []
            p.life = 4
            p.maxlife = 8
            p.dead = False

        self.deck = Deck()

        self.emit_event('simplegame_begin', None)

        try:
            for p in self.players:
                self.process_action(DrawCards(p, amount=4))

            for p in cycle(self.players):
                if not p.dead:
                    self.emit_event('player_turn', p)
                    self.process_action(DrawCardStage(target=p))
                    self.process_action(ActionStage(target=p))
                    self.process_action(DropCardStage(target=p))
        except GameEnded:
            pass

    def game_ended(self):
        return all(p.dead or p.dropped for p in self.players)
