import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
import game
from game import GameError, EventHandler, Action, TimeLimitExceeded
from server_endpoint import Server
from executive import Executive

from utils import DataHolder, BatchList

import logging
log = logging.getLogger('Game_Client')

class TheChosenOne(game.AbstractPlayer):
    dropped = False
    #def __init__(self):
    #    pass
    #    # self.server = server
    #    # self.nickname = server.nickname

    def reveal(self, obj_list):
        # It's me, server will tell me what the hell these is.
        g = Game.getgame()
        st = g.get_synctag()
        raw_data = Executive.server.gexpect('object_sync_%d' % st)
        if isinstance(obj_list, (list, tuple)):
            for o, rd in zip(obj_list, raw_data):
                o.sync(rd)
        else:
            obj_list.sync(raw_data) # it's single obj actually

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

        Executive.server.gwrite(['input_%s_%d' % (tag, st), rst.input])
        return rst.input

class PlayerList(BatchList):
    def user_input_any(self, tag, expects, attachment=None, timeout=25):
        g = Game.getgame()
        st = g.get_synctag()
        tagstr = 'inputany_%s_%d' % (tag, st)

        input = DataHolder()
        input.tag = tag
        input.input = None
        input.attachment = attachment
        input.timeout = timeout
        input.player = g.me

        Break = Exception('Input: you are too late!')

        def waiter_func():
            pid, data = Executive.server.gexpect(tagstr + '_resp')
            self.kill(Break)
            return pid, data

        try:
            waiter = gevent.spawn(waiter_func)
            with gevent.Timeout(timeout):
                g.emit_event('user_input_start', input)
                rst = g.emit_event('user_input', input)
        except (Break, gevent.Timeout):
            g.emit_event('user_input_timeout', input)
            rst = input
            rst.input = None
        finally:
            g.emit_event('user_input_finish', input)

        Executive.server.gwrite([tagstr, rst.input])

        try: waiter.join()
        except Break: pass

        pid, data = waiter.get()

        p = g.player_fromid(pid)

        return p, data

class PeerPlayer(game.AbstractPlayer):
    dropped = False
    def __init__(self, d):
        self.__dict__.update(d)
        game.AbstractPlayer.__init__(self)

    def reveal(self, obj_list):
        # Peer player, won't reveal.
        Game.getgame().get_synctag() # must sync

    def user_input(self, tag, attachement=None, timeout=25):
        # Peer player, get his input from server
        g = Game.getgame()
        st = g.get_synctag()
        input = DataHolder()
        input.timeout = timeout
        input.player = self
        input.input = None
        g.emit_event('user_input_start', input)
        input.input = Executive.server.gexpect('input_%s_%d' % (tag, st))
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
        self.synctag = 0
        self.game_start()

    @staticmethod
    def getgame():
        return getcurrent()

    def get_synctag(self):
        self.synctag += 1
        return self.synctag

class EventHandler(EventHandler):
    game_class = Game

class Action(Action):
    game_class = Game
