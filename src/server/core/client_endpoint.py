from gevent import Greenlet, Timeout
from gevent.queue import Queue
import gamehall as hall
from network import Endpoint, EndpointDied
import logging
import sys

log = logging.getLogger("Client")

__all__ = ['Client']

class Client(Endpoint, Greenlet):
    
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.gdqueue = Queue(100)

    def _run(self):
        cmds = {}
        def handler(*state):
            def register(f):
                for s in state:
                    d = cmds.setdefault(s, {})
                    d[f.__name__] = f
            return register
        
        # --------- Handlers ---------
        @handler('connected')
        def register(self,data):
            self.write(['not_impl', None])
        
        @handler('connected')
        def auth(self, cred):
            name, password = cred
            if password == 'password':
                self.write(['greeting', id(self)])
                self.username = name
                self.nickname = name
                hall.new_user(self)
            else:
                self.write(['auth_err', None])
        
        @handler('hang')
        def create_game(self, name):
            g = hall.create_game(self, name)
            hall.join_game(self, id(g))
        
        @handler('hang')
        def join_game(self, gameid):
            hall.join_game(self, gameid)
    
        @handler('hang')
        def list_game(self, _):
            hall.list_game(self)
        
        @handler('hang')
        def quick_start_game(self, _):
            hall.quick_start_game(self)
        
        @handler('inroomwait')
        def get_ready(self, _):
            hall.get_ready(self)
        
        @handler('inroomwait', 'ready', 'ingame')
        def exit_game(self, _):
            hall.exit_game(self)
        
        @handler('ready')
        def cancel_ready(self, _):
            hall.cancel_ready(self)
        
        @handler('ingame')
        def gamedata(self, data):
            if not self.gdqueue.full():
                self.gdqueue.put(data)
    
        @handler('__any__')
        def _disconnect(self, _):
            self.write(['bye', None])
            self.close()
        
        @handler('__any__')
        def heartbeat(self, _):
            pass
        # --------- End ---------

        self.state = 'connected'
        try:
            while True:
                cmd, data = self.read()
                f = cmds[self.state].get(cmd)
                if not f:
                    f = cmds['__any__'].get(cmd)

                if f:
                    f(self, data)
                else:
                    self.write(['invalid_command', [cmd, data]])
        
        except EndpointDied:
            pass

        except Timeout:
            self.write(['timeout', None])
            self.close()
       
        # client died, do clean ups
        if self.state not in('connected', 'hang'):
            hall.exit_game(self)
    

    def gread(self):
        return self.gdqueue.get()

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
            state=self.state,
        )
