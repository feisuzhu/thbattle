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

    def user_input_any(self, tag, expects, attachment=None, timeout=25):
        g = Game.getgame()
        st = g.get_synctag()
        tagstr = 'inputany_%s_%d' % (tag, st)

        wait_queue = Queue(10)
        pl = PlayerList(p for p in self if not isinstance(p, DroppedPlayer))
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

    def user_input_all(self, tag, process, attachment=None, timeout=25):
        g = Game.getgame()
        st = g.get_synctag()
        workers = BatchList()
        try:
            def worker(p, i):
                while True:
                    input = p.user_input(
                        tag, attachment=attachment, timeout=timeout+10,
                        g=g, st=st*50000+i,
                    )
                    try:
                        input = process(p, input)
                    except ValueError:
                        continue
                    break

            for i, p in enumerate(self):
                workers.append(
                    gevent.spawn(worker, p, i)
                )

            workers.join()
        finally:
            for w in workers:
                w.kill()

class Player(game.AbstractPlayer):
    dropped = False
    def __init__(self, client):
        self.client = client

    def reveal(self, obj_list):
        g = Game.getgame()
        st = g.get_synctag()
        self.client.gwrite('object_sync_%d' % st, obj_list)

    def user_input(self, tag, attachment=None, timeout=25, g=None, st=None):
        g = g if g else Game.getgame()
        st = st if st else g.get_synctag()

        try:
            # The ultimate timeout
            with TimeLimitExceeded(60):
                input = self.client.gexpect('input_%s_%d' % (tag, st))
        except (TimeLimitExceeded, EndpointDied):
            # Player hit the red line, he's DEAD.
            #import gamehall as hall
            #hall.exit_game(self.client)
            input = None
        pl = PlayerList(g.players[:])
        pl.remove(self)
        pl.client.gwrite('input_%s_%d' % (tag, st), input) # tell other players
        return input

    def __data__(self):
        return dict(
            account=self.client.account,
            state=self.client.state,
        )

    @property
    def account(self):
        return self.client.account

class DroppedPlayer(Player):
    dropped = True
    def __data__(self):
        data = Player.__data__(self)
        data['state'] = 'dropped'
        return data

    def reveal(self, obj_list):
        Game.getgame().get_synctag() # must sync

    def user_input(self, tag, attachment=None, timeout=25, g=None, st=None):
        g = g if g else Game.getgame()
        st = st if st else g.get_synctag()
        g.players.client.gwrite('input_%s_%d' % (tag, st), None) # null input

    @property
    def account(self):
        return self.client.account

class Game(Greenlet, game.Game):
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
            nplayers=sum(not (isinstance(p, DroppedPlayer) or p is pph) for p in self.players),
        )

    def __init__(self):
        Greenlet.__init__(self)
        game.Game.__init__(self)
        self.players = []

    def _run(self):
        from server.core import gamehall as hall
        self.synctag = 0
        hall.start_game(self)
        self.game_start()
        hall.end_game(self)

    @staticmethod
    def getgame():
        return getcurrent()

    def get_synctag(self):
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
