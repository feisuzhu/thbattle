# -*- coding: utf-8 -*-
from server_endpoint import Server
import sys
import gevent
from gevent import socket, Greenlet

from utils import DataHolder

from account import Account

import logging
log = logging.getLogger('Executive')

class GameManager(Greenlet):
    '''
    Handles server messages, all game related operations.
    '''
    def __init__(self):
        Greenlet.__init__(self)
        self.state = 'connected'

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
                for i, p in enumerate(data):
                    if p['state'] == 'dropped':
                        self.game.players[i].dropped = True
            self.event_cb('player_change', data)

        @handler(('inroom'), 'ingame')
        def game_started(self, data):
            from client.core import PeerPlayer, TheChosenOne, PlayerList
            pl = [PeerPlayer.parse(i) for i in self.players_data]
            pid = [i.account.userid for i in pl]
            me = TheChosenOne()
            i = pid.index(me.account.userid)
            pl[i] = me
            g = self.game
            g.me = me
            g.players = PlayerList(pl)
            g.start()
            g.link_exception(lambda *a: self.event_cb('game_crashed', g))
            g.link_value(lambda *a: self.event_cb('client_game_finished', g))
            self.event_cb('game_started', g)

        @handler(('hang'), 'inroom')
        def game_joined(self, data):
            self.game = gamemodes[data['type']]()
            Executive.server.gclear()
            self.event_cb('game_joined', self.game)

        @handler(('ingame'), 'hang')
        def fleed(self, data):
            self.game.kill()
            self.game = None
            self.event_cb('fleed')

        @handler(('inroom'), 'hang')
        def game_left(self, data):
            self.game = None
            self.event_cb('game_left')

        @handler(('ingame'), 'hang')
        def end_game(self, data):
            self.event_cb('end_game', self.game)
            self.game = None

        @handler(('connected'), None)
        def auth_result(self, authdata):
            status, data = authdata
            if status == 'success':
                acc = Account.parse(data)
                Executive.account = acc
                self.event_cb('auth_success', acc)
                self.state = 'hang'
            else:
                self.event_cb('auth_failure', data)

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
                if _from: assert self.state in _from
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
                s = socket.socket()
                s.connect(addr)
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
            if not self.state != 'connected':
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
            import settings
            if settings.AUTOUPDATE_ENABLE:
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
                txt = urllib2.urlopen(url).read()
                from client.ui.base import schedule
                schedule(cb, txt)
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
            'kick_user',
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
