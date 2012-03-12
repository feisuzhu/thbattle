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

    def _run(self):
        cmds = {}
        self.heartbeat_cnt = 0
        self.nodata_cnt = 0
        self.timeout = 60
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
                self.nickname = name
                hall.new_user(self)
            else:
                self.write(['auth_result', -1])

        @handler('hang')
        def create_game(self, arg):
            _type, name = arg
            g = hall.create_game(self, _type, name)
            hall.join_game(self, id(g))

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

        @handler('__any__')
        def heartbeat(self, _):
            self.heartbeat_cnt = 0
            self.timeout = 60

        @handler('hang', 'inroomwait', 'ready', 'ingame')
        def chat(self, data):
            hall.chat(self, data)

        @handler('hang', 'inroomwait', 'ready', 'ingame')
        def speaker(self, data):
            hall.speaker(self, data)

        # --------- End ---------

        self.state = 'connected'
        while True:
            try:
                cmd, data = self.read(self.timeout)
                f = cmds[self.state].get(cmd)
                if not f:
                    f = cmds['__any__'].get(cmd)

                if f:
                    f(self, data)
                    if cmd != 'heartbeat': # XXX: hack
                        self.nodata_cnt = 0
                else:
                    self.write(['invalid_command', [cmd, data]])

            except EndpointDied as e:
                self.gdqueue.append(e)
                self.gdevent.set()
                break

            except Timeout:
                self.heartbeat_cnt += 1
                if self.heartbeat_cnt > 1:
                    # drop the client...
                    self.close()
                    break
                self.nodata_cnt += 1
                self.timeout = 15
                if self.nodata_cnt >= 10:
                    # if this guy just keep online but didn't do anything,
                    # drop
                    self.close()
                    break
                self.write(['heartbeat', None])
                continue

        # client died, do clean ups
        if self.state not in('connected', 'hang'):
            hall.exit_game(self)

        if self.state != 'connected':
            hall.user_exit(self)

    def gexpect(self, tag):
        log.info('GAME_EXPECT: %s', repr(tag))
        l = self.gdqueue
        e = self.gdevent
        while True:
            for i in xrange(len(l)):
                d = l.popleft()
                if isinstance(d, EndpointDied):
                    raise d
                elif d[0] == tag:
                    log.info('GAME_READ: %s', repr(d))
                    return d[1]
                else:
                    d.scan_count += 1
                    if d.scan_count >= 5:
                        log.warn('Dropped gamedata: %s' % d)
                    else:
                        log.info('GAME_DATA_MISS: %s', repr(d))
                        l.append(d)
            e.clear()
            e.wait()

    def get_userid(self):
        return id(self)

    def gwrite(self, tag, data):
        self.write(['gamedata', [tag, data]])

    def __data__(self):
        return dict(
            id=id(self),
            username=self.username,
            nickname=self.nickname,
            state=self.state,
        )

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
        which confuse.
        '''
        self.gdqueue.clear()

class DummyClient(object):
    read = write = raw_write = \
    gwrite = gexpect = lambda *a, **k: False

    def __init__(self, client=None):
        if client:
            self.__dict__.update(client.__dict__)
