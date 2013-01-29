# -*- coding: utf-8 -*-
import gevent
from gevent import Greenlet, getcurrent
from gevent.queue import Queue
from gevent.select import select
from game import GameError, EventHandler, Action, TimeLimitExceeded
from client_endpoint import Client, EndpointDied
import game

from utils import BatchList, DataHolder
import logging

log = logging.getLogger('Game_Server')

class PlayerList(BatchList):

    def user_input_any(self, tag, expects, attachment=None, timeout=15):
        g = Game.getgame()
        st = g.get_synctag()
        tagstr = 'inputany_%s_%d' % (tag, st)

        wait_queue = Queue(20)
        pl = PlayerList(p for p in self if not p.dropped)
        n = len(pl)
        def waiter(p):
            try:
                tle = TimeLimitExceeded(timeout+10)
                tle.start()

                data = p.client.gexpect(tagstr)
                wait_queue.put((p, data))
            except (TimeLimitExceeded, EndpointDied) as e:
                if isinstance(e, TimeLimitExceeded) and e is not tle:
                    raise
                wait_queue.put((p, None))
            finally:
                tle.cancel()

        for p in pl:
            gevent.spawn(waiter, p)

        for i in xrange(n):
            p, data = wait_queue.get()
            if expects(p, data):
                break
        else:
            p = None

        if p is None:
            rst_send = rst = [None, None]
        else:
            rst = [p, data]
            rst_send = [g.get_playerid(p), data]

        g.players.client.gwrite(tagstr + '_resp', rst_send)
        return rst

    def user_input_all(self, tag, process, attachment=None, timeout=15):
        g = Game.getgame()
        st = g.get_synctag()
        workers = BatchList()
        try:
            def worker(p, i):
                while True:
                    retry = 0
                    input = p.user_input(
                        tag, attachment=attachment, timeout=timeout,
                        g=g, st=100000 + st*1000 + i*10 + retry,
                    )

                    try:
                        input = process(p, input)
                    except ValueError:
                        retry += 1
                        continue

                    break

            for i, p in enumerate(self):
                w = gevent.spawn(worker, p, i)
                w.game = g
                workers.append(w)

            workers.join()
        finally:
            workers.kill()

class Player(game.AbstractPlayer):
    dropped = False
    def __init__(self, client):
        self.client = client

    def reveal(self, obj_list):
        g = Game.getgame()
        st = g.get_synctag()
        self.client.gwrite('object_sync_%d' % st, obj_list)

    def user_input(self, tag, attachment=None, timeout=15, g=None, st=None):
        g = g if g else Game.getgame()
        st = st if st else g.get_synctag()

        try:
            # The ultimate timeout
            with TimeLimitExceeded(timeout+10):
                input = self.client.gexpect('input_%s_%d' % (tag, st))
        except (TimeLimitExceeded, EndpointDied):
            # Player hit the red line, he's DEAD.
            #import gamehall as hall
            #hall.exit_game(self.client)
            input = None
        pl = PlayerList(g.players[:])
        pl.client.gwrite('input_%s_%d' % (tag, st), input) # tell other players
        return input

    def __data__(self):
        if self.dropped:
            if self.fleed:
                state = 'fleed'
            else:
                state = 'dropped'
        else:
            state = self.client.state

        return dict(
            account=self.client.account,
            state=state,
        )

    @property
    def account(self):
        return self.client.account

class Game(Greenlet, game.Game):
    suicide = False
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''

    CLIENT_SIDE = False
    SERVER_SIDE = True

    def __data__(self):
        from .gamehall import PlayerPlaceHolder as pph
        return dict(
            id=self.gameid,
            type=self.__class__.__name__,
            started=self.game_started,
            name=self.game_name,
            nplayers=sum(not (p is pph or p.dropped) for p in self.players),
        )

    def __init__(self):
        Greenlet.__init__(self)
        game.Game.__init__(self)
        self.players = []

    def _run(self):
        from server.core import gamehall as hall
        self.synctag = 0
        self.game = getcurrent()
        hall.start_game(self)
        self.game_start()
        hall.end_game(self)

    @staticmethod
    def getgame():
        return getcurrent().game
    
    def __repr__(self):
        try:
            gid = str(self.gameid)
        except:
            gid = 'X'

        return '%s:%s' % (self.__class__.__name__, gid)

    def get_synctag(self):
        if self.suicide:
            self.kill()
            return

        self.synctag += 1
        import sys
        if 0: # FOR DEBUG
            t = self.synctag
            expects = [
                set([('reveal', 25, t), ('reveal', 165, t)]),
                set([('reveal', 165, t), ('reveal', 25, t)]),
                set([('user_input', 35, t), ('user_input', 170, t)]),
                set([('user_input', 170, t), ('user_input', 35, t)]),
            ]

            try:
                raise Exception
            except:
                f = sys.exc_info()[2].tb_frame.f_back

            info = (f.f_code.co_name, f.f_lineno, t)
            l = self.players.client.gexpect('synctag_debug')
            l = [tuple(i) for i in l]
            sl = set(l)
            if len(sl) != 1 and sl not in expects:
                print 'SYNC_DEBUG', info, l
                self.players.client.gwrite('in_sync', False)
            else:
                self.players.client.gwrite('in_sync', True)
        return self.synctag

class EventHandler(EventHandler):
    game_class = Game

class Action(Action):
    game_class = Game
