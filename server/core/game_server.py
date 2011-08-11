import gevent
from gevent import Greenlet, Timeout, getcurrent
from gevent.queue import Queue
from game import GameError, EventHandler, Action
from client_endpoint import Client
import game

class TimeLimitExceeded(Timeout):
    pass

class DataHolder(object):
    def __data__(self):
        return self.__dict__

class Player(Client, game.Player):
    pass

class DroppedPlayer(object):
    def __init__(self, player):
        self.__dict__.update(player.__data__())

    def write(self, data):
        pass

    def read(self):
        return ['dropped_player']

    def raw_write(self):
        pass

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
        getcurrent().game = self

    def _run(self):
        from server.core import gamehall as hall
        hall.start_game(self)
        self.game_start()
        hall.end_game(self)

    @staticmethod
    def getgame():
        return getcurrent().game

