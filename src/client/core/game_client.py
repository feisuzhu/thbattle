import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
import game
from game import GameError, EventHandler, Action, TimeLimitExceeded
from server_endpoint import Server

from utils import DataHolder

class Player(Server, game.Player):
    pass

class DroppedPlayer(object):
    def __init__(self, player):
        self.__dict__.update(player.__data__())

class PeerPlayer(object):

    def __init__(self, d):
        self.__dict__.update(d)
        self.gamedata = DataHolder()

class Game(Greenlet, game.Game):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    player_class = Player

    CLIENT_SIDE = True
    SERVER_SIDE = False

    def __init__(self):
        Greenlet.__init__(self)
        self.players = []

    def _run(self):
        getcurrent().game = self
        self.game_start()

    @staticmethod
    def getgame():
        return getcurrent().game

class EventHandler(EventHandler):
    game_class = Game

class Action(Action):
    game_class = Game
