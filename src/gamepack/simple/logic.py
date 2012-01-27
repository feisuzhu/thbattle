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
        for p in self.players:
            p.gamedata.cards = []
            p.gamedata.life = 4
            self.process_action(DrawCards(p, amount=4))

        for p in self.players * 4:
            self.process_action(DrawCardStage(target=p, amount=5))
            self.process_action(ActionStage(target=p))
            self.process_action(DropCardStage(target=p))
