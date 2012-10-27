# -*- coding: utf-8 -*-
import gevent
from gevent import Greenlet
from gevent.queue import Queue
import game
from game import GameError, EventHandler, Action, TimeLimitExceeded
from server_endpoint import Server
from executive import Executive

from utils import DataHolder, BatchList

from account import Account

import logging
log = logging.getLogger('Game_Client')

class TheChosenOne(game.AbstractPlayer):
    dropped = False

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

    def user_input(self, tag, attachment=None, timeout=15, g=None, st=None):
        g = g if g else Game.getgame()
        st = st if st else g.get_synctag()
        input = DataHolder()
        input.tag = tag
        input.input = None
        input.attachment = attachment
        input.timeout = timeout
        input.player = self
        try:
            with gevent.Timeout(timeout+1):
                g.emit_event('user_input_start', input)
                rst = g.emit_event('user_input', input)
        except gevent.Timeout:
            g.emit_event('user_input_timeout', input)
            rst = input

        Executive.server.gwrite('input_%s_%d' % (tag, st), rst.input)
        rst.input = Executive.server.gexpect('input_%s_%d' % (tag, st))
        g.emit_event('user_input_finish', input)
        return rst.input

    @property
    def account(self):
        return Executive.account

    def update(self, data):
        # It's me and I know everything about myself
        pass

class PlayerList(BatchList):

    def user_input_any(self, tag, expects, attachment=None, timeout=15):
        g = Game.getgame()
        st = g.get_synctag()

        tagstr = 'inputany_%s_%d' % (tag, st)

        g.emit_event('user_input_any_begin', (self, tag, attachment))

        input = DataHolder()
        input.tag = tag
        input.input = None
        input.attachment = attachment
        input.timeout = timeout
        input.player = g.me

        class Break(Exception): pass # ('Input: you are too late!')

        def waiter_func():
            pid, data = Executive.server.gexpect(tagstr + '_resp')
            g.kill(Break(), block=False)
            return pid, data

        if isinstance(g.me, TheChosenOne) and g.me in self:
            try:
                waiter = gevent.spawn(waiter_func)
                tle = TimeLimitExceeded(timeout)
                tle.start()
                g.emit_event('user_input_start', input)
                rst = g.emit_event('user_input', input)
                Executive.server.gwrite(tagstr, rst.input)
            except (Break, TimeLimitExceeded) as e:
                if isinstance(e, TimeLimitExceeded) and e is not tle:
                    raise
                g.emit_event('user_input_timeout', input)
                rst = input
                rst.input = None
                Executive.server.gwrite(tagstr, rst.input)
            finally:
                tle.cancel()
                g.emit_event('user_input_finish', input)
                try:
                    waiter.join()
                    gevent.sleep(0)
                except Break:
                    pass

        else:
            # none of my business, just wait for the result
            try:
                waiter = gevent.spawn(waiter_func)
                waiter.join()
                gevent.sleep(0)
            except Break:
                pass

        pid, data = waiter.get()

        g.emit_event('user_input_any_end', tag)

        if pid is None:
            return None, None

        p = g.player_fromid(pid)

        if not expects(p, data):
            raise GameError('WTF?! Server cheats!')

        return p, data

    def user_input_all(self, tag, process, attachment=None, timeout=15):
        g = Game.getgame()
        g.emit_event('user_input_all_begin', (self, tag, attachment))
        st = g.get_synctag()
        workers = BatchList()
        try:
            def worker(p, i):
                while True:
                    input = p.user_input(
                        tag, attachment=attachment, timeout=timeout,
                        g=g, st=st*50000+i,
                    )
                    try:
                        input = process(p, input)
                    except ValueError:
                        continue

                    g.emit_event('user_input_all_data', (tag, p, input))

                    break

            for i, p in enumerate(self):
                workers.append(
                    gevent.spawn(worker, p, i)
                )

            workers.join()
        finally:
            workers.kill()

        g.emit_event('user_input_all_end', tag)

class PeerPlayer(game.AbstractPlayer):
    dropped = False
    def __init__(self):
        game.AbstractPlayer.__init__(self)

    def reveal(self, obj_list):
        # Peer player, won't reveal.
        Game.getgame().get_synctag() # must sync

    def user_input(self, tag, attachment=None, timeout=15, g=None, st=None):
        # Peer player, get his input from server
        g = g if g else Game.getgame()
        st = st if st else g.get_synctag()
        input = DataHolder()
        input.timeout = timeout
        input.player = self
        input.input = None
        input.tag = tag
        g.emit_event('user_input_start', input)
        input.input = Executive.server.gexpect('input_%s_%d' % (tag, st))
        g.emit_event('user_input_finish', input)
        return input.input

    def update(self, data):
        # data comes from server.core.Player.__data__
        self.account = Account.parse(data['account'])
        self.state = data['state']

    @classmethod
    def parse(cls, data):
        pp = cls()
        pp.update(data)
        return pp

    # account = < set by update >

class TheLittleBrother(PeerPlayer):
    _reveal = TheChosenOne.reveal.im_func
    _user_input = PeerPlayer.user_input.im_func
    def reveal(self, *a, **k):
        gevent.sleep(0.1)
        return self._reveal(*a, **k)

    def user_input(self, *a, **k):
        gevent.sleep(0.1)
        return self._user_input(*a, **k)

class Game(Greenlet, game.Game):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    thegame = None
    CLIENT_SIDE = True
    SERVER_SIDE = False

    def __init__(self):
        Greenlet.__init__(self)
        game.Game.__init__(self)
        self.players = PlayerList()
        from .game_client import Game # this class

    def _run(self):
        self.synctag = 0
        Game.thegame = self
        self.game_start()

    @classmethod
    def getgame(cls):
        return cls.thegame
        #return getcurrent()

    def get_synctag(self):
        self.synctag += 1
        # HACK:
        # prevent UI thread from calling
        # this func.
        # since gevent 0.13 can only used in one thread.
        import gevent.hub
        gevent.hub.get_hub()
        if 0: # FOR DEBUG
            import sys
            try:
                raise Exception
            except:
                f = sys.exc_info()[2].tb_frame.f_back

            info = (f.f_code.co_name, f.f_lineno, self.synctag)
            from client.core import Executive
            Executive.server.gwrite('synctag_debug', info)
            ok = Executive.server.gexpect('in_sync')
            if not ok:
                raise Exception('Out of sync')
        return self.synctag

class EventHandler(EventHandler):
    game_class = Game

class Action(Action):
    game_class = Game
