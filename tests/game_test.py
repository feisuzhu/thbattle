# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict
from copy import copy
import logging

# -- third party --
from gevent import Greenlet, getcurrent
import gevent

# -- own --
from endpoint import Endpoint
from game import GameEnded, InputTransaction
from utils import log_failure, instantiate, BatchList
import game

# -- code --
log = logging.getLogger('Game_Test')


def user_input(players, inputlet, timeout=25, type='single', trans=None):
    '''
    Type can be 'single', 'all' or 'any'
    '''
    assert type in ('single', 'all', 'any')
    assert not type == 'single' or len(players) == 1

    timeout = max(0, timeout)

    g = Game.getgame()
    inputlet.timeout = timeout
    players = list(players)

    if not trans:
        with InputTransaction(inputlet.tag(), players) as trans:
            return user_input(players, inputlet, timeout, type, trans)

    t = {'single': '', 'all': '&', 'any': '|'}[type]
    tag = 'I{0}:{1}:'.format(t, inputlet.tag())

    ilets = {p: copy(inputlet) for p in players}
    for p in players:
        ilets[p].actor = p

    results = {p: None for p in players}
    synctags = {p: g.get_synctag() for p in players}

    inputany_player = None

    def get_input_waiter(p, t):
        # should be [tag, <Data for Inputlet.parse>]
        # tag likes 'I?:ChooseOption:2345'
        if p.is_npc:
            ilet = ilets[p]
            p.handle_user_input(trans, ilet)
            return ilet.data()
        else:
            ilet = ilets[p]
            g.test.handle_user_input(p, trans, ilet)
            return ilet.data()

    for p in players:
        g.emit_event('user_input_start', (trans, ilets[p]))

    for p in players:
        stag = tag + str(synctags[p])
        g.test.sync(stag)
        if g.SERVER_SIDE:
            data = get_input_waiter(p, stag)
            g.test.put_sync(stag, data)
        else:
            data = g.test.get_sync(stag)

        my = ilets[p]

        try:
            rst = my.parse(data)
        except:
            log.error('user_input: exception in .process()', exc_info=1)
            # ----- FOR DEBUG -----
            if g.IS_DEBUG:
                raise
            # ----- END FOR DEBUG -----
            rst = None

        rst = my.post_process(p, rst)

        g.emit_event('user_input_finish', (trans, my, rst))

        results[p] = rst

        if type == 'any' and rst is not None:
            assert inputany_player is None
            inputany_player = p

    if type == 'single':
        return results[players[0]]

    elif type == 'any':
        if not inputany_player:
            return None, None

        return inputany_player, results[inputany_player]

    elif type == 'all':
        return OrderedDict([(p, results[p]) for p in players])

    assert False, 'WTF?!'


class Account(object):
    username = ''


class Player(game.AbstractPlayer):
    dropped = False
    fleed   = False
    is_npc  = False

    @property
    def account(self):
        return Account()

    def reveal(self, obj_list):
        g = Game.getgame()
        st = g.get_synctag()
        if g.CLIENT_SIDE:
            raw_data = Game.getgame().test.get_sync(st)
            if g.me is not self:
                return

            if isinstance(obj_list, (list, tuple)):
                for o, rd in zip(obj_list, raw_data):
                    o.sync(rd)
            else:
                obj_list.sync(raw_data)  # it's single obj actually
        else:
            def data(obj):
                return Endpoint.decode(Endpoint.encode(obj))

            Game.getgame().test.put_sync(st, data(obj_list))

    def __data__(self):
        assert False


class NPCPlayer(game.AbstractPlayer):
    dropped = False
    fleed   = False
    is_npc  = True

    def __init__(self, input_handler):
        self.handle_user_input = input_handler

    def reveal(self, obj_list):
        Game.getgame().get_synctag()

    def handle_user_input(self, trans, ilet):
        raise Exception('WTF?!')


class Game(Greenlet, game.Game):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    
    me = None

    import random  # noqa, TODO: replace with patched version

    @instantiate
    class CLIENT_SIDE(object):
        def __get__(self, obj, cls):
            if obj is None:
                obj = cls.getgame()

            return obj.me is not None

    @instantiate
    class SERVER_SIDE(object):
        def __get__(self, obj, cls):
            if obj is None:
                obj = cls.getgame()

            return obj.me is None

    def __init__(self):
        Greenlet.__init__(self)
        game.Game.__init__(self)

    # @log_failure(log)
    def _run(self):
        self.synctag = 0
        self.game = getcurrent()
        pid = self.pid
        params = self.params

        game_params = {k: v[0] for k, v in self.params_def.items()}
        game_params.update(params)

        pl = BatchList([Player() for i in xrange(self.n_persons)])
        self.me = pl[pid] if pid >= 0 else None

        pl[:0] = [NPCPlayer(i.input_handler) for i in self.npc_players]
        self.players = pl

        try:
            self.game_start(game_params)
        except GameEnded:
            pass

        return self.ended

    @staticmethod
    def getgame():
        return getcurrent().game

    def emit_event(self, evt_type, data):
        rst = super(Game, self).emit_event(evt_type, data)
        self.test.handle_event(evt_type, data)
        return rst

    def __repr__(self):
        try:
            gid = str(self.pid) if self.pid >= 0 else 'S'
        except:
            gid = 'X'

        return '%s:%s' % (self.__class__.__name__, gid)

    def get_synctag(self):
        self.synctag += 1
        return self.synctag

    def pause(self, time):
        gevent.sleep(time)
