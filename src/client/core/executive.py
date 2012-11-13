# -*- coding: utf-8 -*-
from server_endpoint import Server
import sys
import gevent
from gevent import socket, Greenlet

from utils import DataHolder

from account import Account

import logging
log = logging.getLogger('Executive')

class ForcedKill(gevent.GreenletExit): pass

class GameManager(Greenlet):
    '''
    Handles server messages, all game related operations.
    '''
    def __init__(self):
        Greenlet.__init__(self)
        self.state = 'connected'
        self.game = None
        self.last_game = None

    def _run(self):
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
                        self.game.players[i].dropped = (p['state'] == 'dropped')

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

            from client.core import PeerPlayer, TheChosenOne, PlayerList
            pl = [PeerPlayer.parse(i) for i in pldata]
            pid = [i.account.userid for i in pl]
            me = TheChosenOne()
            i = pid.index(me.account.userid)
            pl[i] = me
            g = self.game
            g.me = me
            g.players = PlayerList(pl)
            #g.start()
            log.info('=======GAME STARTED=======')
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
            from client.core import PeerPlayer, PlayerList, TheLittleBrother
            pl = [PeerPlayer.parse(i) for i in pldata]
            pid = [i.account.userid for i in pl]
            i = pid.index(tgtid)
            g = self.game
            g.players = PlayerList(pl)
            g.me = g.players[i]
            g.me.__class__ = TheLittleBrother
            #g.start()
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

        @handler(('hang',), 'inroom')
        def game_joined(self, data):
            self.game = gamemodes[data['type']]()
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

        @handler(('hang',), None)
        def your_account(self, accdata):
            Executive.account = acc = Account.parse(accdata)
            self.event_cb('your_account', acc)

        @handler(None, None)
        def thbattle_greeting(self, ver):
            from settings import VERSION
            if ver != VERSION:
                self.event_cb('version_mismatch')
                Executive.call('disconnect')
            else:
                self.event_cb('server_connected', self)

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

class Executive(object):
    '''
    Handles UI commands
    not a Greenlet since main greenlet run this directly.
    '''
    def __init__(self):
        from utils import ITIEvent
        self.event = ITIEvent()
        self.msg_queue = []
        # This callback is called when executive completed a request
        # Called with these args:
        # callback('message', *results)
        self.default_callback = lambda *a, **k: False
        self.state = 'initial' # initial connected

    def call(self, _type, cb=None, *args):
        if not cb:
            cb = self.default_callback
        self.msg_queue.append((_type, cb, args))
        self.event.set()

    def run(self):
        handlers = {}
        def handler(f):
            handlers[f.__name__] = f

        @handler
        def app_exit(self, cb):
            sys.exit()

        @handler
        def connect_server(self, cb, addr, event_cb):
            from client.core import TheChosenOne
            if not self.state == 'initial':
                cb('server_already_connected')
                return
            try:
                s = socket.create_connection(addr)
                svr = Server.spawn(s, 'TheChosenOne')
                self.server = svr
                self.state = 'connected'
                self.gm_greenlet = GameManager()
                self.gm_greenlet.start()
                self.gm_greenlet.event_cb = event_cb

                svr.link_exception(lambda *a: event_cb('server_dropped'))

                #cb('server_connected', svr)
            except:
                cb('server_connect_failed', None)

        @handler
        def disconnect(self, cb):
            if self.state != 'connected':
                cb('not_connected')
                return
            else:
                self.server.close()
                self.state = 'initial'
                self.gm_greenlet.kill()
                self.server = self.gm_greenlet = None
                cb('disconnected')

        @handler
        def update(self, cb, update_cb):
            import autoupdate as au
            from options import options
            import settings
            if not options.no_update:
                base = settings.UPDATE_BASE
                url = settings.UPDATE_URL
                gevent.spawn(lambda: cb(au.do_update(base, url, update_cb)))
            else:
                cb('update_disabled')

        @handler
        def auth(self, cb, arg):
            if not (self.state == 'connected'):
                cb('general_failure', 'Connect first!')
                return
            self.server.write(['auth', arg])

        @handler
        def fetch_resource(self, cb, url):
            def worker():
                import urllib2
                from client.ui.base import schedule
                try:
                    resp = urllib2.urlopen(url)
                    data = resp.read()
                except:
                    schedule(cb, False)
                    return

                schedule(cb, (resp, data))
            gevent.spawn(worker)

        # @handler def register(...): ...
        def simple_gm_op(_type):
            def wrapper(self, cb, *args):
                if not (self.state == 'connected'):
                    cb('general_failure', 'Connect first!')
                    return
                self.server.write([_type, args[0]])
            wrapper.__name__ = _type
            return wrapper
        ops = [
            # FIXME: the quick start thing should be done at client
            'register',     'create_game',      'join_game',
            'get_hallinfo', 'quick_start_game', #'auth',
            'get_ready',    'exit_game',        'cancel_ready',
            'chat',         'speaker',          'change_location',
            'kick_user',    'observe_user',     'query_gameinfo',
            'observe_grant',
        ]
        for op in ops:
            handler(simple_gm_op(op))

        while True:
            self.event.wait()
            for _type, cb, args in self.msg_queue:
                f = handlers.get(_type)
                if f:
                    f(self, cb, *args)
                else:
                    raise Exception('Executive: No such handler: %s' % _type)
            self.msg_queue = []
            self.event.clear()

Executive = Executive()
