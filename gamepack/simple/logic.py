import G
if G.RUNNING == 'Server':
    from server.core import Game, EventHandler, Action, GameError
elif G.RUNNING == 'Client':
    from client.core import Game, EventHandler, Action, GameError
else:
    raise Exception('Where am I?')

from utils import PlayerList
import random
from itertools import count
from cards import Card, HiddenCard
from actions import *

import gevent

class SimpleGame(Game):
    name = 'Simple Game'
    n_persons = 3
    
    def game_start(self):
        if Game.SERVER_SIDE:
            for p in self.players: # game started, every one draw 4 cards.
               p.gamedata.cards = [Card('attack'), Card('attack'), Card('graze'), Card('graze')]
               p.gamedata.life = 4
               p.gwrite(['initial_cards', p.gamedata.cards])
            
            roll = [random.randint(0,100) for i in xrange(3)]
            self.players.gwrite(['roll', roll])

        if Game.CLIENT_SIDE:
            for p in self.players:
                p.gamedata.cards = [HiddenCard] * 4
                p.gamedata.life = 4

            p = Game.getgame().me
            cl = p.gexpect('initial_cards')
            p.gamedata.cards = [Card.parse(i) for i in cl] 


        for p in self.players * 10:
            self.process_action(DrawCardStage(target=p))
            self.process_action(ActionStage(target=p))
            self.process_action(DropCardStage(target=p))
