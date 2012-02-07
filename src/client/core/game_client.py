import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
import game
from game import GameError, EventHandler, Action, TimeLimitExceeded
from server_endpoint import Server

from utils import DataHolder

import logging
log = logging.getLogger('Game_Client')

class TheChosenOne(game.Player):
    dropped = False
    nickname = 'TheChosenOne!' # FOR DEBUG
    def __init__(self, server):
        self.server = server
        #self.nickname = server.nickname

    def reveal(self, obj_list):
        # It's me, server will tell me what the hell these is.
        g = Game.getgame()
        st = g.get_synctag()
        raw_data = self.server.gexpect('object_sync_%d' % st)
        if isinstance(obj_list, (list, tuple)):
            revealed = [ol.__class__.parse(rd) for ol, rd in zip(obj_list, raw_data)]
        else:
            revealed = obj_list.__class__.parse(raw_data)
        return revealed

    def user_input(self, tag, attachment=None, timeout=25):
        g = Game.getgame()
        st = g.get_synctag()
        input = DataHolder()
        input.tag = tag
        input.input = None
        input.attachment = attachment
        input.timeout = timeout
        input.player = self
        try:
            with gevent.Timeout(timeout):
                g.emit_event('user_input_start', input)
                rst = g.emit_event('user_input', input)
        except gevent.Timeout:
            g.emit_event('user_input_timeout', input)
            rst = input
        finally:
            g.emit_event('user_input_finish', input)

        self.server.gwrite(['input_%s_%d' % (tag, st), rst.input])
        return rst.input

class PeerPlayer(game.Player):
    dropped = False
    nickname = 'Youmu!' # FOR DEBUG
    def __init__(self, d):
        self.__dict__.update(d)
        game.Player.__init__(self)

    def reveal(self, obj_list):
        # Peer player, won't reveal.
        Game.getgame().get_synctag() # must sync
        return obj_list

    def user_input(self, tag, attachement=None, timeout=25):
        # Peer player, get his input from server
        g = Game.getgame()
        st = g.get_synctag()
        input = DataHolder()
        input.timeout = timeout
        input.player = self
        input.input = None
        g.emit_event('user_input_start', input)
        input.input = g.me.server.gexpect('input_%s_%d' % (tag, st)) # HACK
        g.emit_event('user_input_finish', input)
        return input.input

class Game(Greenlet, game.Game):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    player_class = TheChosenOne

    CLIENT_SIDE = True
    SERVER_SIDE = False

    def __init__(self):
        Greenlet.__init__(self)
        game.Game.__init__(self)
        self.players = []

    def _run(self):
        getcurrent().game = self
        self.synctag = 0
        self.game_start()

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
