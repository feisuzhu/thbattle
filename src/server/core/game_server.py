import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
from game import GameError, EventHandler, Action, TimeLimitExceeded
from client_endpoint import Client
import game

from utils import PlayerList, DataHolder
import logging

log = logging.getLogger('Game_Server')

class Player(Client, game.Player):

    def reveal(self, obj_list):
        g = Game.getgame()
        st = g.get_synctag()
        self.gwrite(['object_sync_%d' % st, obj_list])
        return obj_list

    def user_input(self, tag, attachment=None):
        g = Game.getgame()
        st = g.get_synctag()
        try:
            # The ultimate timeout
            with TimeLimitExceeded(60):
                input = self.gexpect('input_%s_%d' % (tag, st))
        except TimeLimitExceeded:
            # Player hit the red line, he's DEAD.
            import gamehall as hall
            hall.exit_game(self)
            input = None
        pl = PlayerList(g.players[:])
        pl.remove(self)
        pl.gwrite(['input_%s_%d' % (tag, st), input]) # tell other players
        return input

class DroppedPlayer(object):

    def __init__(self, p):
        self.__dict__.update(p.__dict__)

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

    def reveal(self, obj_list):
        Game.getgame().get_synctag() # must sync
        return obj_list

    def user_input(self, tag, attachment=None):
        g = Game.getgame()
        st = g.get_synctag()
        g.players.gwrite(['input_%s_%d' % (tag, st), None]) # null input

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
            type=self.__class__.__name__,
            started=self.game_started,
            name=self.game_name,
            slots=self.players,
        )
    def __init__(self):
        Greenlet.__init__(self)
        game.Game.__init__(self)
        self.players = []
        self.queue = Queue(100)

    def _run(self):
        from server.core import gamehall as hall
        getcurrent().game = self
        self.synctag = 0
        hall.start_game(self)
        self.game_start()
        hall.end_game(self)

    @staticmethod
    def getgame():
        return getcurrent().game

    def get_synctag(self):
        self.synctag += 1
        return self.synctag

class EventHandler(EventHandler):
    game_class = Game

class Action(Action):
    game_class = Game
