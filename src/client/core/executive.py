from utils import PlayerList
from server_endpoint import Server
import sys
import gevent
from gevent import socket, Greenlet

from utils import DataHolder

import logging
log = logging.getLogger('Executive')

class GameManager(Greenlet):
    '''
    Handles server messages, all game related operations.
    '''
    def __init__(self, server):
        Greenlet.__init__(self)
        self.server = server
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
            if self.state == 'inroom':
                self.players = data
            else:
                for i, p in enumerate(data):
                    if p.get('dropped'):
                        self.game.players[i].dropped = True
            self.event_cb('player_change', data)

        @handler(('inroom'), 'ingame')
        def game_started(self, data):
            from client.core import PeerPlayer, TheChosenOne
            pid = [i['id'] for i in self.players]
            pl = [PeerPlayer(i) for i in self.players]
            #self.server.__class__ = TheChosenOne # FIXME
            pl[pid.index(self.server_id)] = self.server
            self.game.me = self.server
            self.game.players = PlayerList(pl)
            self.server.gamedata = DataHolder()
            self.game.start()
            self.event_cb('game_started', self.game)

        @handler(('hang'), 'inroom')
        def game_joined(self, data):
            self.game = gamemodes[data['type']]()
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
            self.game = None
            self.event_cb('end_game')

        @handler(('connected'), None)
        def auth_result(self, server_id):
            if server_id > 0:
                self.event_cb('auth_success', server_id)
                self.server_id = server_id
                self.state = 'hang'
            else:
                self.event_cb('auth_failure')

        @handler(None, None)
        def invalid_command(self, data):
            self.event_cb('invalid_command', data)

        @handler(None, None)
        def heartbeat(self, _):
            self.server.write(['heartbeat', None])

        @handler(None, None)
        def current_games(self, data):
            self.event_cb('current_games', data)

        while True:
            cmd, data = self.server.ctlexpect(handlers.keys())
            f, _from, _to = handlers.get(cmd)
            if _from: assert self.state in _from
            if f: f(self, data)
            if _to: self.state = _to

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
                svr = TheChosenOne.spawn(s, 'TheChosenOne')
                self.server = svr
                self.state = 'connected'
                self.gm_greenlet = GameManager(self.server)
                self.gm_greenlet.start()
                self.gm_greenlet.event_cb = event_cb
                cb('server_connected', svr)
            except:
                cb('server_connect_failed', None)

        # @handler def register(...): ...
        def simple_gm_op(_type):
            def wrapper(self, cb, *args):
                if not (self.state == 'connected'):
                    cb('general_failure', 'Connect first!')
                    return
                self.server.write([_type, args[0]])
            wrapper.__name__ = _type
            return wrapper
        ops = ['register', 'create_game', 'join_game',
               # FIXME: the quick start thing should be done at client
               'list_game', 'quick_start_game', 'auth',
               'get_ready', 'exit_game', 'cancel_ready']
        for op in ops:
            handler(simple_gm_op(op))

        def no_such_handler(*args):
            raise Exception('Executive: No such handler: %s' % args[0])

        while True:
            self.event.wait()
            for _type, cb, args in self.msg_queue:
                handlers.setdefault(_type, no_such_handler)(self, cb, *args)
            self.msg_queue = []
            self.event.clear()

Executive = Executive()
