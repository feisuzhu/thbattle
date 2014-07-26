# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --
from gevent import socket, Greenlet
import gevent

# -- own --
from account import Account
from network.client import Server
from utils import BatchList, instantiate

# -- code --
log = logging.getLogger('Executive')


class ForcedKill(gevent.GreenletExit):
    pass


class GameManager(Greenlet):
    '''
    Handles server messages, all game related operations.
    '''
    def __init__(self, event_cb):
        Greenlet.__init__(self)
        self.state     = 'connected'
        self.game      = None
        self.last_game = None
        self.event_cb  = event_cb

    def _run(self):
        self.link_exception(lambda *a: self.event_cb('server_dropped'))

        from gamepack import gamemodes
        handlers = {}

        def handler(_from, _to):
            def register(f):
                handlers[f.__name__] = (f, _from, _to)
            return register

        @handler(('inroom', 'ingame'), None)
        def player_change(self, data):
            self.players_data = data
            if self.state == 'ingame':
                data1 = []
                for p in data:
                    acc = Account.parse(p['account'])
                    for i, pl in enumerate(self.game.players):
                        if pl.account.userid != acc.userid: continue
                        data1.append(p)
                        self.game.players[i].dropped = (p['state'] in ('dropped', 'fleed'))

                self.event_cb('player_change', data1)
            else:
                self.event_cb('player_change', data)

        @handler(('inroom',), 'ingame')
        def game_started(self, pldata):
            Executive.server.gclear()
            if self.last_game:
                self.last_game.kill(ForcedKill)
                self.last_game.get()
                self.last_game = None

            from client.core import PeerPlayer, TheChosenOne
            pl = [PeerPlayer.parse(i) for i in pldata]
            pid = [i.account.userid for i in pl]
            me = TheChosenOne(Executive.server)
            me.account = self.account
            i = pid.index(me.account.userid)
            pl[i] = me
            g = self.game
            g.me = me
            g.players = BatchList(pl)
            # g.start()
            log.info('=======GAME STARTED: %d=======' % g.gameid)
            log.info(g)

            @g.link_exception
            def crash(*a):
                self.event_cb('game_crashed', g)

            @g.link_value
            def finish(*a):
                v = g.get()
                if not isinstance(v, ForcedKill):
                    self.event_cb('client_game_finished', g)

            self.event_cb('game_started', g)

        @handler(('inroom',), 'ingame')
        def observe_started(self, data):
            Executive.server.gclear()
            if self.last_game:
                self.last_game.kill(ForcedKill)
                self.last_game.get()
                self.last_game = None

            tgtid, pldata = data
            from client.core import PeerPlayer, TheLittleBrother
            pl = [PeerPlayer.parse(i) for i in pldata]
            pid = [i.account.userid for i in pl]
            i = pid.index(tgtid)
            g = self.game
            g.players = BatchList(pl)
            me = g.players[i]
            me.__class__ = TheLittleBrother
            me.server = Executive.server
            g.me = me
            # g.start()
            log.info('=======OBSERVE STARTED=======')
            log.info(g)

            @g.link_exception
            def crash(*a):
                self.event_cb('game_crashed', g)

            @g.link_value
            def finish(*a):
                v = g.get()
                if not isinstance(v, ForcedKill):
                    self.event_cb('client_game_finished', g)

            self.event_cb('game_started', g)

        @handler(('hang', 'inroom'), 'inroom')
        def game_joined(self, data):
            self.game = gamemodes[data['type']]()
            self.game.gameid = int(data['id'])
            self.event_cb('game_joined', self.game)

        @handler(('ingame',), 'hang')
        def fleed(self, data):
            self.game.kill(ForcedKill)
            self.game = None
            log.info('=======FLEED=======')
            Executive.server.gclear()
            self.event_cb('fleed')

        @handler(('ingame', 'inroom'), 'hang')
        def game_left(self, data):
            self.game.kill(ForcedKill)
            self.game = None
            log.info('=======GAME LEFT=======')
            Executive.server.gclear()
            self.event_cb('game_left')

        @handler(('ingame',), 'hang')
        def end_game(self, data):
            self.event_cb('end_game', self.game)
            log.info('=======GAME ENDED=======')
            self.last_game = self.game

        @handler(('connected',), None)
        def auth_result(self, status):
            if status == 'success':
                self.event_cb('auth_success')
                self.state = 'hang'
            else:
                self.event_cb('auth_failure', status)

        @handler(None, None)
        def your_account(self, accdata):
            self.account = acc = Account.parse(accdata)
            self.event_cb('your_account', acc)

        @handler(None, None)
        def thbattle_greeting(self, ver):
            from settings import VERSION
            if ver != VERSION:
                self.event_cb('version_mismatch')
                Executive.disconnect()
            else:
                self.event_cb('server_connected', self)

        @handler(None, None)
        def ping(self, _):
            Executive.pong()

        @gevent.spawn
        def beater():
            while True:
                gevent.sleep(10)
                Executive.heartbeat()

        while True:
            cmd, data = Executive.server.ctlcmds.get()
            h = handlers.get(cmd)
            if h:
                f, _from, _to = h
                if _from:
                    assert self.state in _from, 'Calling %s in %s state' % (f.__name__, self.state)
                if f: f(self, data)
                if _to: self.state = _to
            else:
                self.event_cb(cmd, data)


@instantiate
class Executive(object):
    def __init__(self):
        self.state = 'initial'  # initial connected

    def connect_server(self, addr, event_cb):
        if not self.state == 'initial':
            return 'server_already_connected'

        try:
            s = socket.create_connection(addr)
            svr = Server.spawn(s, addr)
            svr.link_exception(lambda *a: event_cb('server_dropped'))
            self.server = svr
            self.state = 'connected'
            self.gamemgr = GameManager(event_cb)
            self.gamemgr.start()
            return None

            # return 'server_connected'
        except Exception:
            log.exception('Error connecting server')
            return 'server_connect_failed'

    def disconnect(self):
        if self.state != 'connected':
            return 'not_connected'
        else:
            self.server.close()
            self.state = 'initial'
            self.gamemgr.kill()
            self.server = self.gamemgr = None
            return 'disconnected'

    def update(self, update_cb):
        import autoupdate as au
        from options import options
        import settings
        if not options.no_update:
            base = settings.UPDATE_BASE
            url = settings.UPDATE_URL
            return au.do_update(base, url, update_cb)
        else:
            return 'update_disabled'

    def _simple_op(_type):
        def wrapper(self, *args):
            if not (self.state == 'connected'):
                return 'connect_first'

            self.server.write([_type, args])
        wrapper.__name__ = _type
        return wrapper

    auth            = _simple_op('auth')
    cancel_ready    = _simple_op('cancel_ready')
    change_location = _simple_op('change_location')
    chat            = _simple_op('chat')
    create_game     = _simple_op('create_game')
    exit_game       = _simple_op('exit_game')
    get_lobbyinfo   = _simple_op('get_lobbyinfo')
    get_ready       = _simple_op('get_ready')
    heartbeat       = _simple_op('heartbeat')
    invite_grant    = _simple_op('invite_grant')
    invite_user     = _simple_op('invite_user')
    join_game       = _simple_op('join_game')
    kick_observer   = _simple_op('kick_observer')
    kick_user       = _simple_op('kick_user')
    observe_grant   = _simple_op('observe_grant')
    observe_user    = _simple_op('observe_user')
    pong            = _simple_op('pong')
    query_gameinfo  = _simple_op('query_gameinfo')
    speaker         = _simple_op('speaker')

    del _simple_op
