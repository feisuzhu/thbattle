# -*- coding: utf-8 -*-

import gevent
from gevent import Greenlet, Timeout
from gevent.event import Event
import gamehall as hall
from network import Endpoint, EndpointDied
import logging
import sys

from collections import deque

log = logging.getLogger("Client")

__all__ = ['Client']

class Packet(list): # compare by identity list
    __slots__ = ('scan_count')
    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

    def __ne__(self, other):
        return self.__eq__(other)

class Client(Endpoint, Greenlet):
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.gdqueue = deque(maxlen=100)
        self.gdevent = Event()

        import socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 30)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 6)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)

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
                self.write(['auth_result', self.get_userid()])
                self.username = name
                hall.new_user(self)
            else:
                self.write(['auth_result', -1])

        @handler('hang')
        def create_game(self, arg):
            _type, name = arg
            g = hall.create_game(self, _type, name)
            hall.join_game(self, g.gameid)

        @handler('hang')
        def join_game(self, gameid):
            hall.join_game(self, gameid)

        @handler('hang')
        def get_hallinfo(self, _):
            hall.send_hallinfo(self)

        @handler('hang')
        def quick_start_game(self, _):
            hall.quick_start_game(self)

        @handler('inroomwait')
        def get_ready(self, _):
            hall.get_ready(self)

        @handler('inroomwait', 'ready', 'ingame')
        def exit_game(self, _):
            hall.exit_game(self)

        @handler('inroomwait', 'ready')
        def kick_user(self, uid):
            hall.kick_user(self, uid)

        @handler('inroomwait')
        def change_location(self, loc):
            hall.change_location(self, loc)

        @handler('ready')
        def cancel_ready(self, _):
            hall.cancel_ready(self)

        @handler('ingame')
        def gamedata(self, data):
            p = Packet(data)
            p.scan_count = 0
            self.gdqueue.append(p)
            self.gdevent.set()

        @handler('__any__')
        def _disconnect(self, _):
            self.write(['bye', None])
            self.close()

        @handler('hang', 'inroomwait', 'ready', 'ingame')
        def chat(self, data):
            hall.chat(self, data)

        @handler('hang', 'inroomwait', 'ready', 'ingame')
        def speaker(self, data):
            hall.speaker(self, data)

        # --------- End ---------

        # ----- Banner -----
        from settings import VERSION
        self.write(['thbattle_greeting', VERSION])
        # ------------------

        self.state = 'connected'
        while True:
            try:
                cmd, data = self.read()
                f = cmds[self.state].get(cmd)
                if not f:
                    f = cmds['__any__'].get(cmd)

                if f:
                    f(self, data)
                else:
                    self.write(['invalid_command', [cmd, data]])

            except EndpointDied as e:
                self.gdqueue.append(e)
                self.gdevent.set()
                break

        # client died, do clean ups
        if self.state not in('connected', 'hang'):
            hall.exit_game(self)

        if self.state != 'connected':
            hall.user_exit(self)

    def gexpect(self, tag):
        log.debug('GAME_EXPECT: %s', repr(tag))
        l = self.gdqueue
        e = self.gdevent
        while True:
            for i in xrange(len(l)):
                d = l.popleft()
                if isinstance(d, EndpointDied):
                    raise d
                elif d[0] == tag:
                    log.debug('GAME_READ: %s', repr(d))
                    return d[1]
                else:
                    d.scan_count += 1
                    if d.scan_count >= 15:
                        log.debug('Dropped gamedata: %s' % d)
                    else:
                        log.debug('GAME_DATA_MISS: %s', repr(d))
                        l.append(d)
            e.clear()
            e.wait()

    def get_userid(self):
        return id(self)

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))
        self.write(['gamedata', [tag, data]])

    def __data__(self):
        return [id(self), self.username, self.state]

    def gbreak(self):
        # is it a hack?
        # XXX: definitly, and why it's here?! can't remember
        # Explanation:
        # Well, when sb. exit game in input state,
        # the others must wait until his timeout exceeded.
        # called by gamehall.exit_game to break such condition.
        self.gdqueue.append(EndpointDied())
        self.gdevent.set()

    def gclear(self):
        '''
        Clear the gamedata queue,
        used when a game starts, to eliminate data from last game,
        which confuses the new game.
        '''
        self.gdqueue.clear()

class DummyClient(object):
    read = write = raw_write = \
    gwrite = gexpect = lambda *a, **k: False

    def __init__(self, client=None):
        if client:
            self.__dict__.update(client.__dict__)
