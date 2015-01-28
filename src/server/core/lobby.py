# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from weakref import WeakSet
import atexit
import gzip
import json
import logging
import os
import random
import time

# -- third party --
from gevent import Greenlet, Timeout
from gevent.pool import Pool
from gevent.queue import Empty as QueueEmpty, Queue
import gevent

# -- own --
from account import Account
from endpoint import Endpoint, EndpointDied
from game import Gamedata
from options import options
from settings import VERSION
from utils import BatchList, instantiate, log_failure
from utils.misc import throttle

# -- code --
log = logging.getLogger('Lobby')
__all__ = ['Client']


class Client(Endpoint, Greenlet):
    def __init__(self, sock, addr):
        Endpoint.__init__(self, sock, addr)
        Greenlet.__init__(self)
        self.observers = BatchList()
        self.gamedata = Gamedata()
        self.cmd_listeners = defaultdict(WeakSet)
        self.current_game = None

    @log_failure(log)
    def _run(self):
        self.account = None

        # ----- Banner -----
        from settings import VERSION
        self.write(['thbattle_greeting', VERSION])
        # ------------------

        self.state = 'connected'
        while True:
            try:
                hasdata = False
                with Timeout(90, False):
                    cmd, data = self.read()
                    hasdata = True

                if not hasdata:
                    self.close()
                    # client should send heartbeat periodically
                    raise EndpointDied

                if cmd == 'gamedata':
                    self.gamedata.feed(data)
                else:
                    self.handle_command(cmd, data)

            except EndpointDied:
                self.gbreak()
                break

        # client died, do clean ups
        self.handle_drop()

    def close(self):
        Endpoint.close(self)
        self.kill(EndpointDied)

    def __repr__(self):
        acc = self.account
        if not acc:
            return Endpoint.__repr__(self)

        return '%s:%s:%s' % (
            self.__class__.__name__,
            self.address[0],
            acc.username.encode('utf-8'),
        )

    def __data__(self):
        return dict(
            account=self.account,
            state=self.state,
        )

    def __eq__(self, other):
        return self.account is other.account

    def listen_command(self, *cmds):
        listeners_set = self.cmd_listeners
        q = Queue(100)
        for cmd in cmds:
            listeners_set[cmd].add(q)

        return q

    def handle_command(self, cmd, data):
        f = getattr(self, 'command_' + str(cmd), None)
        if not f:
            listeners = self.cmd_listeners[cmd]
            if listeners:
                [l.put(data) for l in listeners]
                return

            log.debug('No command %s', cmd)
            self.write(['invalid_command', [cmd, data]])
            return

        for_state = getattr(f, 'for_state', None)
        if for_state and self.state not in for_state:
            log.debug('Command %s is for state %s, called in %s', cmd, for_state, self.state)
            self.write(['invalid_command', [cmd, data]])
            return

        if not isinstance(data, (list, tuple)):
            log.error('Malformed command: %s %s', cmd, data)
            return

        n = f.__code__.co_argcount - 1
        if n != len(data):
            log.error(
                'Command "%s" argcount mismatch, expect %s, got %s',
                cmd, n, len(data)
            )
        else:
            f(*data)

    def handle_drop(self):
        if self.state not in ('connected', 'hang'):
            lobby.exit_game(self, is_drop=True)

        if self.state != 'connected':
            lobby.user_leave(self)

    def gexpect(self, tag, blocking=True):
        tag, data = self.gamedata.gexpect(tag, blocking)
        if tag:
            manager = GameManager.get_by_user(self)
            manager.record_user_gamedata(self, tag, data)

        return tag, data

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s -> %s', self.account.username, repr([tag, data]))

        manager = GameManager.get_by_user(self)
        manager.record_gamedata(self, tag, data)

        encoded = self.encode(['gamedata', [tag, data]])
        self.raw_write(encoded)
        self.observers and self.observers.raw_write(encoded)

    def gbreak(self):
        return self.gamedata.gbreak()

    def gclear(self):
        self.gamedata = Gamedata()

    def for_state(*state):
        def register(f):
            f.for_state = state
            return f

        return register

    # --------- Handlers ---------
    @for_state('connected')
    def command_auth(self, login, password):
        if self.account:
            self.write(['invalid_command', ['auth', '']])
            return

        acc = Account.authenticate(login, password)
        if acc:
            self.account = acc
            if not acc.available():
                self.write(['auth_result', 'not_available'])
                self.close()
            else:
                self.write(['auth_result', 'success'])
                self.account = acc
                lobby.user_join(self)

        else:
            self.write(['auth_result', 'invalid_credential'])

    @for_state('hang')
    def command_create_game(self, _type, name):
        manager = lobby.create_game(self, _type, name)
        manager and lobby.join_game(self, manager.gameid)

    @for_state('hang')
    def command_quick_start_game(self):
        lobby.quick_start_game(self)

    @for_state('hang')
    def command_join_game(self, gameid):
        lobby.join_game(self, gameid)

    def command_get_lobbyinfo(self):
        lobby.send_lobbyinfo(self)

    @for_state('hang')
    def command_observe_user(self, uid):
        lobby.observe_user(self, uid)

    @for_state('hang')
    def command_query_gameinfo(self, gid):
        lobby.send_gameinfo(self, gid)

    @for_state('inroomwait')
    def command_get_ready(self):
        lobby.get_ready(self)

    @for_state('inroomwait')
    def command_set_game_param(self, key, value):
        lobby.set_game_param(self, key, value)

    @for_state('inroomwait', 'ready', 'ingame', 'observing')
    def command_exit_game(self):
        lobby.exit_game(self)

    @for_state('inroomwait', 'ready')
    def command_kick_user(self, uid):
        lobby.kick_user(self, uid)

    @for_state('inroomwait', 'ready')
    def command_invite_user(self, uid):
        lobby.invite_user(self, uid)

    @for_state('inroomwait', 'ready', 'ingame')
    def command_kick_observer(self, uid):
        lobby.kick_observer(self, uid)

    @for_state('inroomwait', 'observing')
    def command_change_location(self, loc):
        lobby.change_location(self, loc)

    @for_state('ready')
    def command_cancel_ready(self):
        lobby.cancel_ready(self)

    def command_heartbeat(self):
        pass

    @for_state('hang', 'inroomwait', 'ready', 'ingame', 'observing')
    def command_chat(self, text):
        lobby.chat(self, text)

    @for_state('hang', 'inroomwait', 'ready', 'ingame', 'observing')
    def command_speaker(self, text):
        lobby.speaker(self, text)

    del for_state
    # --------- End handlers ---------


class DroppedClient(Client):
    read = write = raw_write = gclear = lambda *a, **k: None

    def __init__(self, client=None):
        client and self.__dict__.update(client.__dict__)

    def __data__(self):
        return dict(
            account=self.account,
            state='left',
        )

    def gwrite(self, tag, data):
        manager = GameManager.get_by_user(self)
        manager.record_gamedata(self, tag, data)

    def gexpect(self, tag, blocking=True):
        raise EndpointDied

    @property
    def state(self):
        return 'dropped'

    @state.setter
    def state(self, val):
        pass


class NPCClient(Client):
    read = write = raw_write = gclear = lambda *a, **k: None
    state = property(lambda: 'ingame')

    def __init__(self, name):
        acc = Account.build_npc_account(name)
        self.account = acc

    def __data__(self):
        return dict(
            account=self.account,
            state='ingame',
        )

    def gwrite(self, tag, data):
        pass

    def gexpect(self, tag, blocking=True):
        raise Exception('Should not be called!')

'''
User state machine:
     [Observing]     --------------<------------<-----------
          |          |                                     |
    -> [Hang] <-> [InRoomWait] <-> [Ready] -> [InGame] -->----
        |                  |         |             |
        --->[[Disconnect]]<-------------------------
'''


class Lobby(object):
    def __init__(self, current_gid=0):
        # should use WeakSet or WeakValueDictionary,
        # but this works fine, not touching it.
        self.games = {}  # all games
        self.users = {}  # all users
        self.dropped_users = {}  # passively dropped users
        self.current_gid = current_gid

    def new_gid(self):
        self.current_gid += 1
        return self.current_gid

    @throttle(1.5)
    def refresh_status(self):
        ul = [u for u in self.users.values() if u.state == 'hang']
        Pool(5).map_async(self.send_lobbyinfo, ul)
        interconnect.publish('current_users', self.users.values())
        interconnect.publish('current_games', self.games.values())

    def send_lobbyinfo(self, user):
        user.write(['current_games', self.games.values()], Client.FMT_COMPRESSED)
        user.write(['current_users', self.users.values()], Client.FMT_COMPRESSED)
        user.write(['your_account', user.account])

    def user_join(self, user):
        uid = user.account.userid

        user.state = 'hang'
        user.observing = None
        log.info(u'User %s joined, online user %d' % (user.account.username, len(self.users)))

        if uid in self.users:
            # squeeze the original one out
            log.info('%s has been squeezed out' % user.account.username)
            old = self.users[uid]
            user.account = old.account
            old.close()  # this forces a drop, will call exit_game

            manager = GameManager.get_by_user(old)
            manager and manager.squeeze_out(old, user)

        elif uid in self.dropped_users:
            log.info(u'%s rejoining dropped game' % user.account.username)
            old = self.dropped_users.pop(uid)
            assert isinstance(old, DroppedClient), 'Arghhhhh'

            self.send_lobbyinfo(user)

            manager = GameManager.get_by_user(old)
            manager.reconnect(user)

        self.users[uid] = user

        self.refresh_status()

        return True

    def user_leave(self, user):
        uid = user.account.userid
        self.users.pop(uid, 0)
        log.info(u'User %s leaved, online user %d' % (user.account.username, len(self.users)))
        self.refresh_status()

    def create_game(self, user, gametype, name):
        from gamepack import gamemodes
        if gametype not in gamemodes:
            user.write(['lobby_error', 'gametype_not_exist'])
            return

        gid = self.new_gid()
        gamecls = gamemodes[gametype]
        manager = GameManager(gid, gamecls, name)
        self.games[gid] = manager
        log.info("Create game")
        self.refresh_status()

        return manager

    def join_game(self, user, gameid, slot=None):
        if user.state in ('hang', 'observing') and gameid in self.games:
            manager = self.games[gameid]
        else:
            user.write(['lobby_error', 'cant_join_game'])
            return

        if manager.is_banned(user):
            user.write(['lobby_error', 'banned'])
            return

        log.info("join game")

        manager.join_game(user, slot, observing=user.state == 'observing')
        self.refresh_status()

    def clear_observers(self, user):
        obs = user.observers[:]
        user.observers[:] = []

        for ob in obs:
            ob.state = 'hang'
            ob.observing = None

        for ob in obs:
            ob.write(['game_left', None])

    def try_remove_empty_game(self, manager):
        if manager.gameid not in self.games:
            return

        if manager.get_online_users():
            return

        if manager.game_started:
            log.info('game aborted')
            manager.archive()
        else:
            log.info('game canceled')

        for u in manager.users:
            if u is ClientPlaceHolder:
                continue
            self.dropped_users.pop(u.account.userid, 0)

        manager.kill_game()
        self.games.pop(manager.gameid, None)

    def start_game(self, manager):
        log.info("game started")
        manager.start_game()
        self.refresh_status()

    def quick_start_game(self, user):
        if user.state != 'hang':
            user.write(['lobby_error', 'cant_join_game'])
            return

        for manager in self.games.values():
            if manager.next_free_slot() is not None:
                self.join_game(user, manager.gameid)
                return
        else:
            user.write(['lobby_error', 'cant_join_game'])

    def end_game(self, manager):
        log.info("end game")
        manager.archive()

        all_dropped = not bool(manager.get_online_users())

        if not all_dropped:
            bonus = manager.get_bonus()

            for u, t, v in bonus:
                u.account.add_credit(t, v)

        for u in manager.users:
            u.gclear()  # clear game data
            self.dropped_users.pop(u.account.userid, 0)

        manager.end_game()
        self.games.pop(manager.gameid, 0)

        if all_dropped:
            return

        new_mgr = self.create_game(None, manager.gamecls.__name__, manager.game_name)
        for u in manager.users:
            self.join_game(u, new_mgr.gameid)

        new_mgr.update_game_param(manager.game_params)
        self.refresh_status()

    def exit_game(self, user, is_drop=False):
        manager = GameManager.get_by_user(user)
        if user.state == 'observing':
            manager.observe_leave(user)

        elif user.state != 'hang':
            dummy = manager.exit_game(user, is_drop)

            if is_drop and user.state == 'ingame':
                self.dropped_users[user.account.userid] = dummy

            user.state = 'hang'
            self.clear_observers(user)
            self.try_remove_empty_game(manager)
            self.refresh_status()
        else:
            user.write(['lobby_error', 'not_in_a_game'])

    def send_gameinfo(self, user, gid):
        manager = self.games.get(gid)
        if not manager:
            return

        manager.send_gameinfo(user)

    def change_location(self, user, loc):
        manager = GameManager.get_by_user(user)
        if user.state == 'inroomwait':
            manager.change_location(user, loc)
            self.refresh_status()
        elif user.state == 'observing':
            self.join_game(user, manager.gameid, loc)

    def set_game_param(self, user, key, value):
        if user.state != 'inroomwait':
            return

        manager = GameManager.get_by_user(user)
        manager.set_game_param(user, key, value)
        self.refresh_status()

    def kick_user(self, user, uid):
        other = self.users.get(uid)
        if not other:
            return

        manager = GameManager.get_by_user(user)
        if manager.kick_user(user, other):
            self.exit_game(other)

    def kick_observer(self, user, uid):
        other = self.users.get(uid)
        if not other:
            return

        manager = GameManager.get_by_user(user)
        if manager.kick_observer(user, other):
            self.exit_game(other)

    def get_ready(self, user):
        manager = GameManager.get_by_user(user)
        manager.get_ready(user)
        self.refresh_status()

    def cancel_ready(self, user):
        manager = GameManager.get_by_user(user)
        manager.cancel_ready(user)
        self.refresh_status()

    def observe_user(self, user, other_userid):
        other = self.users.get(other_userid, None)

        if not other:
            user.write(['lobby_error', 'no_such_user'])
            return

        if other.state == 'observing':
            other = other.observing

        if other.state not in ('ingame', 'inroomwait', 'ready'):
            user.write(['lobby_error', 'user_not_ingame'])
            return

        @gevent.spawn
        def worker():
            with Timeout(20, False):
                rst = None
                other.write(['observe_request', [user.account.userid, user.account.username]])
                chan = other.listen_command('observe_grant')
                while True:
                    rst = chan.get()
                    if rst is None:
                        return

                    try:
                        ob_id, grant = rst
                    except:
                        continue

                    if ob_id != user.account.userid:
                        continue

                    break

            if not (rst and
                    user.state == 'hang' and
                    other.state in ('ingame', 'inroomwait', 'ready')):
                return

            if grant:
                if other.state not in ('ingame', 'inroomwait', 'ready'):
                    user.write(['lobby_error', 'user_not_ingame'])
                else:
                    manager = GameManager.get_by_user(other)
                    manager.observe_user(user, other)
                    self.refresh_status()
            else:
                user.write(['observe_refused', other.account.username])

        worker.gr_name = 'OB:[%r] -> [%r]' % (user, other)

    def invite_user(self, user, other_userid):
        if user.account.userid < 0:
            gevent.spawn(user.write, ['system_msg', [None, u'毛玉不能使用邀请功能']])
            return

        other = self.users.get(other_userid, None)

        if not (other and other.state in ('hang', 'observing')):
            user.write(['lobby_error', 'user_not_found'])
            return

        manager = GameManager.get_by_user(user)

        @gevent.spawn
        def worker():
            with Timeout(20, False):
                other.write(['invite_request', [
                    user.account.userid,
                    user.account.username,
                    manager.gameid,
                    manager.gamecls.__name__,
                ]])

                rst = None
                chan = other.listen_command('invite_grant')
                gid = grant = 0

                while True:
                    rst = chan.get()
                    if rst is None:
                        return

                    try:
                        gid, grant = rst
                    except:
                        continue

                    if gid != manager.gameid:
                        continue

                    break

            if not (grant and gid in self.games and not manager.game_started and other.state != 'ingame'):
                # granted, game not cancelled or started
                return

            if manager.next_free_slot() is None:
                # no free space
                return

            if other.state in ('inroomwait', 'ready') and other.current_game is manager:
                # same game
                return

            self.join_game(other, gid)

        worker.gr_name = 'Invite:[%r] -> [%r]' % (user, other)

    def chat(self, user, msg):
        @log_failure(log)
        def worker():
            manager = GameManager.get_by_user(user)

            if msg.startswith('!!') and (options.freeplay or user.account.userid in (2, 3044)):
                # admin commands
                cmd = msg[2:]
                if cmd == 'stacktrace':
                    manager.record_stacktrace()
                elif cmd == 'clearzombies':
                    self.clearzombies()
                elif cmd == 'ping':
                    self.ping(user)

                return

            packed = (user.account.username, msg)
            if user.state == 'hang':  # lobby chat
                for u in self.users.values():
                    if u.state == 'hang':
                        u.write(['chat_msg', packed])

            elif user.state in ('inroomwait', 'ready', 'ingame', 'observing'):  # room chat
                ul = manager.users
                obl = BatchList()
                map(obl.__iadd__, ul.observers)
                _type = 'ob_msg' if user.state == 'observing' else 'chat_msg'
                ul.write([_type, packed])  # should be here?
                obl.write([_type, packed])

        worker.gr_name = 'chat worker for %s' % user.account.username
        gevent.spawn(worker)

    def speaker(self, user, msg):
        @gevent.spawn
        def worker():
            if user.account.other['credits'] < 10:
                user.write(['system_msg', [None, u'您的节操掉了一地，文文不愿意帮你散播消息。']])
            else:
                user.account.add_credit('credits', -10)
                interconnect.publish('speaker', [user.account.username, msg])

        log.info(u'Speaker: %s', msg)

    def system_msg(self, msg):
        @gevent.spawn
        def worker():
            for u in self.users.values():
                u.write(['system_msg', [None, msg]])

    def clearzombies(self):
        for i, u in self.users.items():
            if u.ready():
                log.info('Clear zombie: %r', u)
                self.users.pop(i, 0)

    def ping(self, user):
        manager = GameManager.get_by_user(user)
        if manager:
            clients = manager.get_online_users()
        else:
            clients = self.users.values()

        def ping(p):
            chan = p.listen_command('pong')
            b4 = time.time()
            p.write(['ping', None])
            try:
                chan.get(timeout=5)
                t = time.time() - b4
                t *= 1000
                user.write(['system_msg', [None, u'%s %fms' % (p.account.username, t)]])
            except QueueEmpty:
                user.write(['system_msg', [None, u'%s 超时' % p.account.username]])

        for p in clients:
            gevent.spawn(ping, p)


if options.gidfile and os.path.exists(options.gidfile):
    last_gid = int(open(options.gidfile, 'r').read())
else:
    last_gid = 0

lobby = Lobby(last_gid)


@instantiate
class ClientPlaceHolder(object):
    state     = 'left'
    account   = None
    observers = BatchList()
    raw_write = write = lambda *a: False

    def __data__(self):
        return (None, None, 'left')


class GameManager(object):

    def __init__(self, gid, gamecls, name):
        g = gamecls()

        self.game         = g
        self.users        = BatchList([ClientPlaceHolder] * g.n_persons)
        self.game_started = False
        self.game_name    = name
        self.banlist      = defaultdict(set)
        self.gameid       = gid
        self.gamecls      = gamecls
        self.game_params  = {k: v[0] for k, v in gamecls.params_def.items()}

        g.gameid    = gid
        g.manager   = self
        g.rndseed   = random.getrandbits(63)
        g.random    = random.Random(g.rndseed)
        g.gr_groups = WeakSet()

    def __data__(self):
        return {
            'id':       self.gameid,
            'type':     self.gamecls.__name__,
            'started':  self.game_started,
            'name':     self.game_name,
            'nplayers': len(self.get_online_users()),
            'params':   self.game_params,
        }

    @classmethod
    def get_by_user(cls, user):
        '''
        Get GameManager object for user.

        :rtype: GameManager
        '''

        return user.current_game

    def send_gameinfo(self, user):
        g = self.game
        user.write(['gameinfo', [g.gameid, g.players]])

    @throttle(0.1)
    def notify_playerchange(self):
        @gevent.spawn
        def notify():
            from server.core.game_server import Player

            pl = self.game.players if self.game_started else map(Player, self.users)
            s = Client.encode(['player_change', pl])
            for cl in self.users:
                cl.raw_write(s)
                cl.observers and cl.observers.raw_write(s)

    def next_free_slot(self):
        try:
            return self.users.index(ClientPlaceHolder)
        except ValueError:
            return None

    def archive(self):
        g = self.game
        if not options.archive_path:
            return

        data = []

        data.append('# ' + ', '.join([
            p.account.username.encode('utf-8')
            for p in self.users
        ]))

        data.append('# Ver: ' + VERSION)
        data.append('# GameId: ' + str(self.gameid))
        s, e = int(self.start_time), int(time.time())
        data.append('# Time: start = %d, end = %d, elapsed = %d' % (s, e, e - s))

        data.append(self.gamecls.__name__)
        data.append(json.dumps(self.game_params))
        data.append(str(g.rndseed))
        data.append(json.dumps(self.usergdhistory))
        data.append(json.dumps(self.gdhistory))

        f = gzip.open(os.path.join(options.archive_path, str(self.gameid)) + '.gz', 'wb')
        f.write('\n'.join(data))
        f.close()

    def get_ready(self, user):
        if user.state not in ('inroomwait',):
            return

        g = self.game
        if user not in self.users:
            log.error('User not in player list')
            return

        user.state = 'ready'
        self.notify_playerchange()

        if all(u.state == 'ready' for u in self.users):
            if not g.started:
                # race condition here.
                # wrap in 'if g.started' to prevent double starting.
                log.info("game starting")
                g.start()

    def cancel_ready(self, user):
        if user.state not in ('ready',):
            return

        if user not in self.users:
            log.error('User not in player list')
            return

        user.state = 'inroomwait'
        self.notify_playerchange()

    def set_game_param(self, user, key, value):
        if user.state != 'inroomwait':
            return

        if user not in self.users:
            log.error('User not in this game!')
            return

        cls = self.gamecls
        if key not in cls.params_def:
            log.error('Invalid option "%s"', key)
            return

        if value not in cls.params_def[key]:
            log.error('Invalid value "%s" for key "%s"', value, key)
            return

        if self.game_params[key] == value:
            return

        self.game_params[key] = value

        for u in self.users:
            if u.state == 'ready':
                self.cancel_ready(u)

            u.write(['set_game_param', [user, key, value]])
            u.write(['game_params', self.game_params])

        self.notify_playerchange()

    def update_game_param(self, params):
        self.game_params.update(params)
        self.users.write(['game_params', self.game_params])
        self.notify_playerchange()

    def change_location(self, user, loc):
        if user.state not in ('inroomwait', ):
            return

        pl = self.users
        if (not 0 <= loc < len(pl)) or (pl[loc] is not ClientPlaceHolder):
            user.write(['change_loc_failed', None])
            return

        # observing: should send join game
        i = pl.index(user)
        pl[loc], pl[i] = pl[i], pl[loc]
        self.notify_playerchange()

    def kick_user(self, user, other):
        if user.state not in ('inroomwait', 'ready'):
            return

        cl = self.users

        bl = self.banlist[other]
        bl.add(user)
        cl.write(['kick_request', [user, other, len(bl)]])
        return len(bl) >= len(cl) // 2

    def kick_observer(self, user, other):
        if user not in self.users:
            return False

        if GameManager.get_by_user(other) is not self:
            return False

        if other.state != 'observing':
            return False

        return True

    def observe_leave(self, user, no_move=False):
        assert user.state == 'observing'

        tgt = user.observing
        tgt.observers.remove(user)
        user.state = 'hang'
        user.observing = None
        user.current_game = None
        user.gclear()
        no_move or user.write(['game_left', None])

        @gevent.spawn
        def notify_observer_leave():
            ul = self.users
            info = [user.account.userid, user.account.username, tgt.account.username]
            ul.write(['observer_leave', info])
            for obl in ul.observers:
                obl and obl.write(['observer_leave', info])

    def observe_user(self, user, observee):
        g = self.game
        assert observee in self.users
        assert user.state == 'hang'

        log.info("observe game")

        observee.observers.append(user)

        user.state = 'observing'
        user.current_game = self
        user.observing = observee
        user.write(['game_joined', self])
        user.gclear()  # clear stale gamedata

        self.notify_playerchange()

        @gevent.spawn
        def notify_observer():
            ul = self.users
            info = [user.account.userid, user.account.username, observee.account.username]
            ul.write(['observer_enter', info])
            for obl in ul.observers:
                obl and obl.write(['observer_enter', info])

        if g.started:
            user.write(['observe_started', [self.game_params, observee.account.userid, self.build_initial_players()]])
            self.replay(user, observee)
        else:
            self.notify_playerchange()

    def is_banned(self, user):
        return len(self.banlist[user]) >= max(self.game.n_persons // 2, 1)

    def join_game(self, user, slot, observing=False):
        assert user not in self.users
        assert user.state == ('observing' if observing else 'hang')

        if slot is None:
            slot = self.next_free_slot()
        elif self.users[slot] is not ClientPlaceHolder:
            slot = None

        if slot is None:
            return

        self.users[slot] = user

        if observing:
            origin = self.get_by_user(user)
            origin.observe_leave(user, no_move=origin is self)

        user.current_game = self
        user.state = 'inroomwait'
        user.write(['game_joined', self])
        if user.observers:
            for ob in user.observers:
                ob.write(['game_joined', self])
                ob.current_game = self
                ob.state = 'observing'

        self.notify_playerchange()

    def start_game(self):
        g = self.game
        assert ClientPlaceHolder not in self.users
        assert all([u.state == 'ready' for u in self.users])

        self.game_started = True

        g.players = self.build_initial_players()

        self.usergdhistory = []
        self.gdhistory     = [list() for p in self.users]

        self.start_time = time.time()
        for u in self.users:
            u.write(["game_started", [self.game_params, g.players]])
            u.gclear()
            if u.observers:
                u.observers.gclear()
                u.observers.write(['observe_started', [self.game_params, u.account.userid, g.players]])
            u.state = 'ingame'

    def build_initial_players(self):
        from server.core.game_server import Player, NPCPlayer

        pl = BatchList([Player(u) for u in self.users])
        pl[:0] = [NPCPlayer(NPCClient(i.name), i.input_handler) for i in self.game.npc_players]

        return pl

    def record_gamedata(self, user, tag, data):
        idx = self.users.index(user)
        self.gdhistory[idx].append((tag, Client.decode(Client.encode(data))))

    def record_user_gamedata(self, user, tag, data):
        idx = self.users.index(user)
        self.usergdhistory.append((idx, tag, Client.decode(Client.encode(data))))

    def replay(self, observer, observee):
        idx = self.users.index(observee)
        for data in self.gdhistory[idx]:
            observer.write(['gamedata', data])

    def squeeze_out(self, old, new):
        old.write(['others_logged_in', None])
        if old.state == 'ingame':
            self.reconnect(new)

    def reconnect(self, new):
        g = self.game
        new.state = 'ingame'
        new.current_game = self

        for p in g.players:
            if p.client.account.userid == new.account.userid:
                p.reconnect(new)
                break
        else:
            assert False, 'Oops'

        for i, u in enumerate(self.users):
            if u.account.userid == new.account.userid:
                self.users[i] = new
                break
        else:
            assert False, 'Oops'

        new.write(['game_joined',  self])
        self.notify_playerchange()

        players = self.build_initial_players()
        new.write(['game_started', [self.game_params, players]])

        self.replay(new, new)

    def exit_game(self, user, is_drop):
        rst = None
        assert user in self.users
        is_drop or user.gclear()
        g = self.game
        if self.game_started:
            i = g.players.client.index(user)
            p = g.players[i]
            log.info('player dropped')
            if g.can_leave(p):
                user.write(['game_left', None])
                p.set_fleed(False)
            else:
                if not is_drop:
                    user.write(['fleed', None])
                    p.set_fleed(True)
                else:
                    p.set_fleed(False)

            p.client.gbreak()  # XXX: fuck I forgot why it's here. Exp: see comment on Client.gbreak
            p.set_dropped()
            dummy = DroppedClient(g.players[i].client)
            p.set_client(dummy)
            self.users.replace(user, dummy)
            rst = dummy
        else:
            log.info('player leave')
            self.users.replace(user, ClientPlaceHolder)
            user.write(['game_left', None])

        self.notify_playerchange()

        for bl in self.banlist.values():
            bl.discard(user)

        return rst

    def end_game(self):
        for u in self.users:
            u.write(['end_game', None])
            u.observers and u.observers.write(['end_game', None])
            u.state = 'hang'

    def get_online_users(self):
        return [p for p in self.users if (p is not ClientPlaceHolder and not isinstance(p, DroppedClient))]

    def kill_game(self):
        self.game.suicide = True  # game will kill itself in get_synctag()

    def get_bonus(self):
        assert self.get_online_users()

        t = time.time()
        g = self.game
        percent = min(1.0, (t - self.start_time) / 1200)
        import math
        rate = math.sin(math.pi / 2 * percent)
        winners = g.winners
        bonus = g.n_persons * 5 / len(winners) if winners else 0

        rst = []

        for p in g.players:
            u = p.client

            if isinstance(u, NPCClient):
                continue

            rst.append((u, 'games', 1))
            if p.dropped or p.fleed:
                if not options.no_counting_flee:
                    rst.append((u, 'drops', 1))
            else:
                s = 5 + bonus if p in winners else 5
                rst.append((u, 'credits', int(s * rate * options.credit_multiplier)))

        return rst

    def record_stacktrace(self):
        g = self.game
        log.info('>>>>> GAME STACKTRACE <<<<<')

        def logtraceback(gr):
            import traceback
            log.info('----- %r -----\n%s', gr, ''.join(traceback.format_stack(gr.gr_frame)))

        logtraceback(g)
        for i in g.gr_groups:
            for j in i:
                logtraceback(j)

        for cl in g.players.client:
            if isinstance(cl, Client):
                logtraceback(cl)

        log.info('===========================')


if options.interconnect:
    from utils.interconnect import Interconnect

    class InterconnectHandler(Interconnect):
        def on_message(self, node, topic, message):
            if topic == 'speaker':
                node = node if node != options.node else ''
                message.insert(0, node)
                Pool(5).map_async(lambda u: u.write(['speaker_msg', message]), lobby.users.values())

    interconnect = InterconnectHandler.spawn(options.node, options.redis_url)

else:
    class DummyInterconnect(object):
        def publish(self, key, message):
            pass

    interconnect = DummyInterconnect()


@atexit.register
def _exit_handler():
    # logout all the accounts
    # to save the credits
    for u in lobby.users.values():
        u.account.add_credit('credits', 50)

    # save gameid
    fn = options.gidfile
    if fn:
        with open(fn, 'w') as f:
            f.write(str(lobby.current_gid + 1))
