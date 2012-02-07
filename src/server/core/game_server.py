import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
from game import GameError, EventHandler, Action, TimeLimitExceeded
from client_endpoint import Client, EndpointDied
import game

from utils import BatchList, DataHolder
import logging

log = logging.getLogger('Game_Server')

class Player(game.Player):
    dropped = False
    def __init__(self, client):
        self.client = client

    def reveal(self, obj_list):
        g = Game.getgame()
        st = g.get_synctag()
        self.client.gwrite(['object_sync_%d' % st, obj_list])

    def user_input(self, tag, attachment=None, timeout=25):
        g = Game.getgame()
        st = g.get_synctag()
        try:
            # The ultimate timeout
            with TimeLimitExceeded(60):
                print "INPUT!"
                input = self.client.gexpect('input_%s_%d' % (tag, st))
        except (TimeLimitExceeded, EndpointDied):
            # Player hit the red line, he's DEAD.
            import gamehall as hall
            hall.exit_game(self.client)
            input = None
        pl = BatchList(g.players[:])
        pl.remove(self)
        pl.client.gwrite(['input_%s_%d' % (tag, st), input]) # tell other players
        return input

    def __data__(self):
        return dict(
            id=id(self.client),
            username=self.client.username,
            nickname=self.client.nickname,
            state=self.client.state,
        )

class DroppedPlayer(Player):
    dropped = True
    def __data__(self):
        return dict(
            username=self.client.username,
            nickname=self.client.nickname,
            id=-1,
        )

    def reveal(self, obj_list):
        Game.getgame().get_synctag() # must sync

    def user_input(self, tag, attachment=None, timeout=25):
        g = Game.getgame()
        st = g.get_synctag()
        g.players.client.gwrite(['input_%s_%d' % (tag, st), None]) # null input

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
