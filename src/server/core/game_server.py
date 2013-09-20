# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict
from copy import copy
import time
import logging
log = logging.getLogger('Game_Server')


# -- third party --
from gevent import Greenlet, getcurrent
import gevent

# -- own --
from network.server import EndpointDied
from game import TimeLimitExceeded, InputTransaction
from utils import waitany, log_failure
from network.common import GamedataMixin
import game

# -- code --


def user_input(players, inputlet, timeout=25, type='single', trans=None):
    '''
    Type can be 'single', 'all' or 'any'
    '''
    assert type in ('single', 'all', 'any')
    assert not type == 'single' or len(players) == 1

    g = Game.getgame()
    inputlet.timeout = timeout
    players = players[:]

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

    evmap = {p.client.gdevent: p for p in players}

    def get_input():
        # should be [tag, <Data for Inputlet.parse>]
        # tag likes 'I?:ChooseOption:2345'

        # try for data in buffer
        for p in players:
            try:
                _, rst = p.client.gexpect(tag + str(synctags[p]), blocking=False)
                if rst is not GamedataMixin.NODATA:
                    return p, rst
            except EndpointDied:
                return p, None

        # wait for new data
        ev = waitany([p.client.gdevent for p in players])
        assert ev
        assert ev.is_set()

        p = evmap[ev]
        try:
            _, rst = p.client.gexpect(tag + str(synctags[p]), blocking=False)
            assert rst is not GamedataMixin.NODATA

        except EndpointDied:
            return p, None

        return p, rst

    orig_players = players[:]

    till = time.time() + timeout + 5
    try:
        inputany_player = None

        for p in players:
            g.emit_event('user_input_start', (trans, ilets[p]))

        while players:
            # NOTICE: This is a must.
            # TLE would be raised at other part (notably my.post_process) in the original solution
            # (wrapping large parts of code in 'with TimeLimitExceeded(): ...')
            with TimeLimitExceeded(max(till - time.time(), 0)):
                p, data = get_input()

            g.players.client.gwrite('R{}{}'.format(tag, synctags[p]), data)

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

            players.remove(p)
            results[p] = rst

            if type == 'any' and rst is not None:
                inputany_player = p
                break

    except TimeLimitExceeded:
        pass

    # timed-out players
    for p in players:
        g.emit_event('user_input_finish', (trans, ilets[p], None))
        g.players.client.gwrite('R{}{}'.format(tag, synctags[p]), None)

    if type == 'single':
        return results[orig_players[0]]

    elif type == 'any':
        if not inputany_player:
            return None, None

        return inputany_player, results[inputany_player]

    elif type == 'all':
        return OrderedDict([(p, results[p]) for p in orig_players])

    assert False, 'WTF?!'


class Player(game.AbstractPlayer):
    dropped = False

    def __init__(self, client):
        self.client = client

    def reveal(self, obj_list):
        g = Game.getgame()
        st = g.get_synctag()
        self.client.gwrite('Sync:%d' % st, obj_list)

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

    @log_failure(log)
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
        return self.synctag

    def pause(self, time):
        gevent.sleep(time)
