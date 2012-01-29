from game.autoenv import Game, EventHandler, Action, GameError

from utils import PlayerList
import random
from itertools import count
from cards import Card, HiddenCard
from actions import *

import logging
log = logging.getLogger('SimpleGame')

class SimpleGame(Game):
    name = 'Simple Game'
    n_persons = 2

    if Game.CLIENT_SIDE:
        # not loading these things on server
        from ui import SimpleGameUI as ui_class

    def game_start(self):
        # game started, init state

        class PlayerQueue(object):
            def __init__(self, players, repeat=-1, initial=0):
                self.players = players
                self.index = initial
                self.count = repeat * len(players)

            def __iter__(self):
                return self

            def next(self):
                if not self.count:
                    raise StopIteration
                self.count -= 1
                i = self.index
                self.index = (i+1) % len(self.players)
                return self.players[i]

        # Do not do this:
        # for p in self.players: blah-blah....
        # since players can leave game and become DroppedPlayers
        for p in PlayerQueue(self.players, 1):
            p.gamedata.cards = []
            p.gamedata.life = 4
            self.process_action(DrawCards(p, amount=4))

        self.emit_event('simplegame_begin', None)

        for p in PlayerQueue(self.players):
            self.process_action(DrawCardStage(target=p))
            self.process_action(ActionStage(target=p))
            self.process_action(DropCardStage(target=p))
