from game.autoenv import Game, EventHandler, Action, GameError

from utils import PlayerList
import random
from itertools import count
from cards import Card, HiddenCard
from actions import *
from ui import SimpleGameUI

import gevent

class SimpleGame(Game):
    name = 'Simple Game'
    n_persons = 1

    ui_class = SimpleGameUI

    def game_start(self):
        # game started, init state
        for p in self.players:
            p.gamedata.cards = []
            p.gamedata.life = 4
            self.process_action(DrawCards(p, amount=4))

        for p in self.players * 2:
            self.process_action(DrawCardStage(target=p))
            self.process_action(ActionStage(target=p))
            self.process_action(DropCardStage(target=p))
