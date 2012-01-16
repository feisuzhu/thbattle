import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
from game import GameError, EventHandler, Action, TimeLimitExceeded
from client_endpoint import Client
import game

class DataHolder(object):
    def __data__(self):
        return self.__dict__

class Player(Client, game.Player):
    pass

class DroppedPlayer(Player):
    
    def __data__(self):
        return dict(
            username=self.username,
            nickname=self.nickname,
            id=1,
            dropped=True,
        )

    def gwrite(self, d): pass
    def gexpect(self, d): raise TimeLimitExceeded
    def gread(self): raise TimeLimitExceeded
    def write(self, d): pass
    def raw_write(self, d): pass

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
    
    CLIENT_SIDE = False
    SERVER_SIDE = True

    def __data__(self):
        from server.core import UserPlaceHolder
        return dict(
            id=id(self),
            type=self.__class__.name,
            empty_slots=self.players.count(UserPlaceHolder),
        )
    def __init__(self):
        Greenlet.__init__(self)
        self.players = []
        self.queue = Queue(100)

    def _run(self):
        from server.core import gamehall as hall
        getcurrent().game = self
        hall.start_game(self)
        self.game_start()
        hall.end_game(self)

    @staticmethod
    def getgame():
        return getcurrent().game

class EventHandler(EventHandler):
    game_class = Game

class Action(Action):
    game_class = Game
