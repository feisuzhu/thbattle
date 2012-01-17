from utils import PlayerList
from server_endpoint import Server
import sys
import gevent
from gevent import socket, Greenlet

from utils import DataHolder

class ServerEvents(Greenlet):
    def __init__(self, server, server_id):
        Greenlet.__init__(self)
        self.server = server
        self.server_id = server_id
        self.state = 'hang'

    def _run(self):
        from client.core import PeerPlayer
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

        @handler(('inroom'), 'ingame')
        def game_started(self, data):
            pid = [i['id'] for i in self.players]
            pl = [PeerPlayer(i) for i in self.players]
            pl[pid.index(self.server_id)] = self.server
            self.game.me = self.server
            self.game.players = PlayerList(pl)
            self.server.gamedata = DataHolder()
            self.game.start()

        @handler(('hang'), 'inroom')
        def game_joined(self, data):
            self.game = gamemodes[data['type']]()

        @handler(('ingame'), 'hang')
        def fleed(self, data):
            self.game.kill()
            self.game = None

        @handler(('inroom'), 'hang')
        def game_left(self, data):
            self.game = None

        @handler(('ingame'), 'hang')
        def end_game(self, data):
            self.game = None

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
        self.state = 'initial' # initial connected authed(now in game)

    def message(self, _type, cb=None, *args):
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
        def connect_server(self, cb, addr):
            if not self.state == 'initial':
                cb('server_already_connected')
                return
            try:
                s = socket.socket()
                s.connect(addr)
                svr = Server.spawn(s, 'SERVER')
                self.server = svr
                self.state = 'connected'
                def heartbeat():
                    while True:
                        gevent.sleep(30)
                        self.server.write(['heartbeat', None])
                self.heartbeat_greenlet = gevent.spawn(heartbeat)
                cb('server_connected', svr)
            except:
                cb('server_connect_failed', None)

        @handler
        def authenticate(self, cb, user, pwd):
            if not (self.state == 'connected'):
                cb('auth_failure', 'Connect first!')
                return
            self.server.write(['auth', [user, pwd]])
            rst, data = self.server.ctlexpect(['greeting', 'auth_err'])
            if rst == 'greeting':
                server_id = data
                self.state = 'hang'
                self.serverevents_greenlet = ServerEvents(self.server, server_id)
                self.serverevents_greenlet.start()
                self.state = 'authed'
                cb('authenticated', server_id)
            else:
                cb('auth_failure', 'Incorrect user/pwd!')

        def no_such_handler(*args):
            #raise Exception('No such handler: %s' % args[0])
            print 'Executive: no such handler: %s' % args[0]

        while True:
            self.event.wait()
            for _type, cb, args in self.msg_queue:
                handlers.setdefault(_type, no_such_handler)(self, cb, *args)
            self.event.clear()

Executive = Executive()
