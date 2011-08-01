from gevent import Greenlet
from gevent.queue import Queue
from server.core import User
from server.core import gamehall as hall
import logging
import sys

log = logging.getLogger("Receptionist")

class Receptionist(Greenlet):
    
    def _client_died(self, G):
        self.quit = True
        self.command('QUIT', None)
        log.debug("client died")
    
    def __init__(self, client):
        super(self.__class__, self).__init__()
        self.client = client
        client.receptionist = self
        client.rawlink(self._client_died)
        self.wait_channel = Queue(10)
        self.quit = False

    def _run(self):
        u = self.client
        # TODO: auth / register
        u.state = 'connected'
        u.__class__ = User
                
        u.active_queue = self.wait_channel
        
        def wrap(f, has_p):
            u = self.client
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
            },

            '__any__': {
                'heartbeat':        lambda *args, **kwargs: 1,
                'disconnect':       self._disconnect,
            },
        }
        while True:
            cmd, data = self.wait_channel.get()
            if cmd == 'QUIT' and self.quit:
                log.debug('QUIT received.')
                break
            f = cmds[u.state].get(cmd)
            if not f:
                f = cmds['__any__'].get(cmd)

            if f:
                f(data)
            else:
                u.write(['invalid_command'])
       
        # client died, do clean ups
        if u.state not in('connected', 'hang'):
            hall.exit_game(self.client)
    
    def _notimpl(self,data):
        self.client.write(['not_impl', None])
        
    def _auth(self, cred):
        u = self.client
        name,nick = cred
        u.write(['greeting','Hello %s!' % nick])
        u.username = name
        u.nickname = nick
        hall.new_user(u)
    
    def _create_game(self, name):
        g = hall.create_game(self.client, name)
        hall.join_game(self.client, id(g))

    def _disconnect(self, _):
        hall.exit_game(self.client)
        self.client.write(['bye', None])
        self.client.close()
    
    def command(self, cmd, data):
        self.wait_channel.put([cmd, data])
