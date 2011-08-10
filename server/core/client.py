from gevent import Greenlet, Timeout
from gevent.queue import Queue
import gamehall as hall
from network import Endpoint, EndpointDied
import logging
import sys

log = logging.getLogger("Client")

class Client(Endpoint, Greenlet):
    
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.gdqueue = Queue(100)

    def _run(self):
        self.state = 'connected'
                
        def wrap(f, has_p):
            u = self
            def _wrapper(data):
                if has_p:
                    f(u, data)
                else:
                    f(u)
            return _wrapper

        cmds = {
            'connected': {
                'auth':             self._auth,
                'register':         self._notimpl,
            },

            'hang': {
                'create_game':      self._create_game,
                'join_game':        wrap(hall.join_game, 1),
                'list_game':        wrap(hall.list_game, 0),
                'quick_start_game': wrap(hall.quick_start_game, 0),
            },

            'inroomwait': {
                'get_ready':        wrap(hall.get_ready, 0),
                'exit_game':        wrap(hall.exit_game, 0),
            },

            'ready': {
                'cancel_ready':     wrap(hall.cancel_ready, 0),
                'exit_game':        wrap(hall.exit_game, 0),
            },

            'ingame': {
                'exit_game':        wrap(hall.exit_game, 0),
                'gamedata':         self._gamedata,
            },

            '__any__': {
                'heartbeat':        lambda *args, **kwargs: 1,
                'disconnect':       self._disconnect,
            },
        }
        try:
            while True:
                cmd, data = self.read()
                f = cmds[self.state].get(cmd)
                if not f:
                    f = cmds['__any__'].get(cmd)

                if f:
                    f(data)
                else:
                    self.write(['invalid_command', None])
        
        except EndpointDied:
            pass

        except Timeout:
            self.write(['timeout', None])
            self.close()
       
        # client died, do clean ups
        if self.state not in('connected', 'hang'):
            hall.exit_game(self)
    
    def _notimpl(self,data):
        self.write(['not_impl', None])
        
    def _auth(self, cred):
        name,nick = cred
        self.write(['greeting','Hello %s!' % nick])
        self.username = name
        self.nickname = nick
        hall.new_user(self)
    
    def _create_game(self, name):
        g = hall.create_game(self, name)
        hall.join_game(self, id(g))

    def _disconnect(self, _):
        self.write(['bye', None])
        self.close()
    
    def _gamedata(self, data):
        if not self.gdqueue.full():
            self.gdqueue.put(data)

    def gread(self):
        d = self.gdqueue.get()
        assert d[0] == 'gamedata', "What? It's impossible!"
        return d[1]

    def gexpect(self, tag):
        while True:
            d = self.gread()
            if d[0] == tag:
                return d[1]
           #else: drop
    
    def gwrite(self, data):
        self.write(['gamedata', data])

    def __data__(self):
        return dict(
            id=id(self),
            username=self.username,
            nickname=self.nickname,
            halldata=self.halldata if hasattr(self, 'halldata') else None,
            state=self.state,
        )
