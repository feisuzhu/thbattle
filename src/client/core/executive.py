# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --
from gevent import Greenlet, socket
from gevent.pool import Pool
from gevent.queue import Channel
import gevent

# -- own --
from .replay import Replay
from account import Account
from autoupdate import Autoupdate
from endpoint import Endpoint
from game import Gamedata
from utils import BatchList, instantiate


# -- code --
log = logging.getLogger('Executive')


class Server(Endpoint, Greenlet):
    '''
    Used at client side, to represent server
    '''

    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.ctlcmds = Channel()
        self.userid = 0
        self.gamedata = Gamedata(recording=True)

    def _run(self):
        while True:
            cmd, data = self.read()
            if cmd == 'gamedata':
                self.gamedata.feed(data)
            else:
                self.ctlcmds.put([cmd, data])

    def gexpect(self, tag, blocking=True):
        return self.gamedata.gexpect(tag, blocking)

    def gbreak(self):
        return self.gamedata.gbreak()

    def gclear(self):
        self.gamedata = Gamedata(recording=True)

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))
        encoded = self.encode(['gamedata', [tag, data]])
        self.raw_write(encoded)

    def wait_till_live(self):
        self.gamedata.wait_empty()

    def gamedata_piled(self):
        return len(self.gamedata.gdqueue) > 60

    def shutdown(self):
        self.kill()
        self.join()
        self.ctlcmds.put(['shutdown', None])
        self.close()


class ReplayEndpoint(object):
    def __init__(self, replay, game):
        self.gdlist = list(replay.gamedata)
        self.game = game

    def gexpect(self, tag):
        if not self.gdlist:
            gevent.sleep(3)
            raise ForcedKill

        glob = False
        if tag.endswith('*'):
            tag = tag[:-1]
            glob = True

        for i, d in enumerate(self.gdlist):
            if d[0] == tag or (glob and d[0].startswith(tag)):
                del self.gdlist[i]
                return d

        gevent.sleep(3)
        raise ForcedKill

    def gwrite(self, tag, data):
        pass

    def gclear(self):
        pass

    def gbreak(self):
        pass

    def end_replay(self):
        self.game.kill()


class ForcedKill(gevent.GreenletExit):
    pass


class GameManager(Greenlet):
    '''
    Handles server messages, all game related operations.
    '''
    def __init__(self, event_cb):
        Greenlet.__init__(self)
        self.state          = 'connected'
        self.game           = None
        self.last_game      = None
        self.last_game_info = None
        self.last_replay    = None
        self.event_cb       = event_cb
        self.server_name    = 'OFFLINE'

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
        def game_started(self, data):
            params, pldata = data
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
            g.game_params = params
            g.players = BatchList(pl)
            # g.start()  Starts by UI
            log.info('=======GAME STARTED: %d=======' % g.gameid)
            log.info(g)

            self.last_game_info = params, i, pldata

            @g.link_exception
            def crash(*a):
                self.event_cb('game_crashed', g)

            @g.link_value
            def finish(*a):
                v = g.get()
                if not isinstance(v, ForcedKill):
                    self.event_cb('client_game_finished', g)

            self.event_cb('game_started', (g, params, pldata, g.players[:]))

        @handler(('inroom',), 'ingame')
        def observe_started(self, data):
            Executive.server.gclear()
            if self.last_game:
                self.last_game.kill(ForcedKill)
                self.last_game.get()
                self.last_game = None

            params, tgtid, pldata = data
            from client.core import PeerPlayer, TheLittleBrother
            pl = [PeerPlayer.parse(i) for i in pldata]
            pid = [i.account.userid for i in pl]
            i = pid.index(tgtid)
            self.last_game_info = params, i, pldata
            g = self.game
            g.players = BatchList(pl)
            me = g.players[i]
            me.__class__ = TheLittleBrother
            me.server = Executive.server
            g.me = me
            g.game_params = params
            # g.start()  Starts by UI
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

            self.event_cb('game_started', (g, params, pldata, g.players[:]))

        @handler(('hang', 'inroom'), 'inroom')
        def game_joined(self, data):
            self.game = gamemodes[data['type']]()
            self.game.gameid = int(data['id'])
            self.event_cb('game_joined', self.game)
            self.event_cb('game_params', data['params'])

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
            g = self.game
            self.event_cb('end_game', g)
            log.info('=======GAME ENDED=======')
            self.last_game = g

            rep = Replay()
            rep.client_version = Executive.get_current_version()
            rep.game_mode = g.__class__.__name__
            params, i, pldata = self.last_game_info
            rep.game_params = params
            rep.me_index = i
            rep.users = pldata
            rep.gamedata = Executive.server.gamedata.history
            rep.track_info = {
                'server': Executive.gamemgr.server_name,
                'gameid': g.gameid,
            }
            self.last_replay = rep

        @handler(('connected',), None)
        def auth_result(self, status):
            if status == 'success':
                self.event_cb('auth_success')
                self.state = 'hang'
            else:
                self.event_cb('auth_failure', status)

        @handler(None, None)
        def your_account(self, accdata):
            self.accdata = accdata
            self.account = Account.parse(accdata)
            self.event_cb('your_account', accdata)

        @handler(None, None)
        def thbattle_greeting(self, data):
            from settings import VERSION

            try:
                name, ver = data

            except ValueError:
                name, ver = 'UNKNOWN', data

            if ver != VERSION:
                self.event_cb('version_mismatch')
                Executive.disconnect()
            else:
                self.server_name = name
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
            if cmd == 'shutdown':
                beater.kill()
                break

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
            self.state = 'connecting'
            s = socket.create_connection(addr)
            self.server = svr = Server.spawn(s, addr)
            svr.link_exception(lambda *a: event_cb('server_dropped'))
            self.gamemgr = GameManager(event_cb)
            self.state = 'connected'
            self.gamemgr.start()
            return None

            # return 'server_connected'
        except Exception:
            self.state = 'initial'
            log.exception('Error connecting server')
            return 'server_connect_failed'

    def disconnect(self):
        if self.state != 'connected':
            return 'not_connected'
        else:
            self.state = 'dying'
            loop = gevent.getcurrent() is self.gamemgr

            @gevent.spawn
            def kill():
                self.server.shutdown()
                self.gamemgr.join()
                self.server = self.gamemgr = None
                self.state = 'initial'

            if not loop:
                kill.join()

            return 'disconnected'

    def update(self, update_cb):
        from options import options
        import settings
        if options.no_update:
            return 'update_disabled'

        errord = [False]

        def do_update(name, path, server):
            up = Autoupdate(path)
            try:
                for p in up.update(server):
                    update_cb(name, p)
            except Exception as e:
                log.exception(e)
                errord[0] = True
                update_cb('error', e)

        pool = Pool(2)

        pool.spawn(do_update, 'logic_progress', settings.LOGIC_UPDATE_BASE, settings.LOGIC_UPDATE_SERVER)
        if settings.INTERPRETER_UPDATE_BASE:
            pool.spawn(do_update, 'interpreter_progress', settings.INTERPRETER_UPDATE_BASE, settings.INTERPRETER_UPDATE_SERVER)

        pool.join()

        return 'updated' if not errord[0] else 'error'

    def switch_version(self, version):
        import settings
        up = Autoupdate(settings.LOGIC_UPDATE_BASE)
        return up.switch(version)

    def is_version_match(self, version):
        import settings
        up = Autoupdate(settings.LOGIC_UPDATE_BASE)
        return up.is_version_match(version)

    def get_current_version(self):
        import settings
        up = Autoupdate(settings.LOGIC_UPDATE_BASE)
        return up.get_current_version()

    def is_version_present(self, version):
        import settings
        up = Autoupdate(settings.LOGIC_UPDATE_BASE)
        return up.is_version_present(version)

    def save_replay(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.gamemgr.last_replay.dumps())

    def start_replay(self, rep, event_cb):
        assert self.state == 'initial'

        self.state = 'replay'

        from client.core import PeerPlayer, TheLittleBrother
        from gamepack import gamemodes

        g = gamemodes[rep.game_mode]()
        self.server = ReplayEndpoint(rep, g)

        pl = [PeerPlayer.parse(i) for i in rep.users]

        g.players = BatchList(pl)
        me = g.players[rep.me_index]
        me.__class__ = TheLittleBrother
        me.server = self.server
        g.me = me
        g.game_params = rep.game_params
        log.info('=======REPLAY STARTED=======')

        # g.start()  Starts by UI

        @g.link_exception
        def crash(*a):
            self.state = 'initial'
            event_cb('game_crashed', g)

        @g.link_value
        def finish(*a):
            self.state = 'initial'
            v = g.get()
            if not isinstance(v, ForcedKill):
                event_cb('client_game_finished', g)

            event_cb('end_game', g)

        return g

    def end_replay(self):
        assert self.state == 'replay'
        self.server.end_replay()
        self.server = None

    def _simple_op(_type):
        def wrapper(self, *args):
            if not (self.state == 'connected'):
                return 'connect_first'

            self.server.write([_type, args])
        wrapper.__name__ = _type
        return wrapper

    auth             = _simple_op('auth')
    cancel_ready     = _simple_op('cancel_ready')
    change_location  = _simple_op('change_location')
    chat             = _simple_op('chat')
    create_game      = _simple_op('create_game')
    exit_game        = _simple_op('exit_game')
    get_lobbyinfo    = _simple_op('get_lobbyinfo')
    get_ready        = _simple_op('get_ready')
    heartbeat        = _simple_op('heartbeat')
    invite_grant     = _simple_op('invite_grant')
    invite_user      = _simple_op('invite_user')
    join_game        = _simple_op('join_game')
    kick_observer    = _simple_op('kick_observer')
    kick_user        = _simple_op('kick_user')
    observe_grant    = _simple_op('observe_grant')
    observe_user     = _simple_op('observe_user')
    pong             = _simple_op('pong')
    query_gameinfo   = _simple_op('query_gameinfo')
    quick_start_game = _simple_op('quick_start_game')
    set_game_param   = _simple_op('set_game_param')
    speaker          = _simple_op('speaker')

    del _simple_op
