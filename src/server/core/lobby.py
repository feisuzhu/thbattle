# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import atexit
import logging
import os
import shlex
import time

# -- third party --
from gevent import Timeout
from gevent.pool import Pool
from gevent.queue import Empty as QueueEmpty
import gevent

# -- own --
from options import options
from server.core.endpoint import Client, DroppedClient
from server.core.game_manager import GameManager
from server.subsystem import Subsystem
from utils import BatchList, log_failure
from utils.misc import throttle
from utils.stats import stats


# -- code --
log = logging.getLogger('Lobby')
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
        self.games = {}          # all games
        self.users = {}          # all users
        self.dropped_users = {}  # passively dropped users
        self.current_gid = current_gid
        self.admins = [2, 109, 351, 3044, 6573, 6584, 9783]
        self.bigbrothers = []

        self.lobby_command_dispatch = {
            'create_game':      self.create_game_and_join,
            'quick_start_game': self.quick_start_game,
            'join_game':        self.join_game,
            'get_lobbyinfo':    self.get_lobbyinfo,
            'observe_user':     self.observe_user,
            'query_gameinfo':   self.send_gameinfo,
            'get_ready':        self.get_ready,
            'set_game_param':   self.set_game_param,
            'use_item':         self.use_item,
            'exit_game':        self.exit_game,
            'kick_user':        self.kick_user,
            'invite_user':      self.invite_user,
            'kick_observer':    self.kick_observer,
            'change_location':  self.change_location,
            'cancel_ready':     self.cancel_ready,
            'chat':             self.chat,
            'speaker':          self.speaker,
        }

    def _command(for_state, argstype):
        def decorate(f):
            f._contract = (for_state, argstype)
            return f

        return decorate

    def process_command(self, user, cmd, args):
        dispatch = self.lobby_command_dispatch

        handler = dispatch.get(cmd)

        if not handler:
            log.info('Unknown command %s', cmd)
            user.write(['invalid_lobby_command', [cmd, args]])
            return

        for_state, argstype = handler._contract

        if for_state and user.state not in for_state:
            log.debug('Command %s is for state %s, called in %s', cmd, for_state, user.state)
            user.write(['invalid_lobby_command', [cmd, args]])
            return

        if not (len(argstype) == len(args) and all(isinstance(v, t) for t, v in zip(argstype, args))):
            log.debug('Command %s with wrong args, expecting %r, actual %r', cmd, argstype, args)
            user.write(['invalid_lobby_command', [cmd, args]])
            return

        handler(user, *args)

    def new_gid(self):
        self.current_gid += 1
        return self.current_gid

    @throttle(1.5)
    def refresh_status(self):
        ul = [u for u in self.users.values() if u.state == 'hang']
        self.send_lobbyinfo(ul)
        Subsystem.interconnect.publish('current_users', self.users.values())
        Subsystem.interconnect.publish('current_games', self.games.values())

    @_command(None, [])
    def get_lobbyinfo(self, user):
        self.send_lobbyinfo([user])

    def send_lobbyinfo(self, ul):
        d = Client.encode([
            ['current_games', self.games.values()],
            ['current_users', self.users.values()],
        ], Client.FMT_BULK_COMPRESSED)

        p = Pool(6)

        @p.spawn
        def send():
            for u in ul:
                @p.spawn
                def send_single(u=u):
                    u.raw_write(d)
                    self.send_account_info(u)

    def send_account_info(self, user):
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

        if uid in self.dropped_users:
            log.info(u'%s rejoining dropped game' % user.account.username)
            old = self.dropped_users.pop(uid)
            assert isinstance(old, DroppedClient), 'Arghhhhh'

            @gevent.spawn
            def reconnect():
                self.send_account_info(user)

                manager = GameManager.get_by_user(old)
                manager.reconnect(user)

        self.users[uid] = user

        self.refresh_status()

        return True

    def user_leave(self, user):
        uid = user.account.userid
        self.users.pop(uid, 0)
        log.info(u'User %s left, online user %d' % (user.account.username, len(self.users)))
        self.refresh_status()

    @_command(['hang'], [basestring, unicode, bool])
    def create_game_and_join(self, user, gametype, name, invite_only):
        manager = self.create_game(user, gametype, name, invite_only)
        manager.add_invited(user)
        manager and self.join_game(user, manager.gameid)

    def create_game(self, user, gametype, name, invite_only):
        from thb import modes, modes_maoyu
        if user and user.account.is_maoyu() and gametype not in modes_maoyu:
            user.write(['message_err', 'maoyu_limitation'])
            return

        if gametype not in modes:
            user.write(['message_err', 'gametype_not_exist'])
            return

        gid = self.new_gid()
        gamecls = modes[gametype]
        manager = GameManager(gid, gamecls, name, invite_only)
        self.games[gid] = manager
        log.info("Create game")
        self.refresh_status()

        return manager

    @_command(['hang'], [int])
    def join_game(self, user, gameid, slot=None):
        if user.state in ('hang', 'observing') and gameid in self.games:
            manager = self.games[gameid]
        else:
            user.write(['message_err', 'cant_join_game'])
            return

        from thb import modes_maoyu
        if user.account.is_maoyu() and manager.gamecls.__name__ not in modes_maoyu:
            user.write(['message_err', 'maoyu_limitation'])
            return

        if manager.is_banned(user):
            user.write(['message_err', 'banned'])
            return

        if not manager.is_invited(user):
            user.write(['message_err', 'not_invited'])
            return

        log.info("join game")

        # TOO HACKY, PAL
        observing = user.state == 'observing'
        manager.join_game(user, slot, observing=observing)
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
            u.account and self.dropped_users.pop(u.account.userid, 0)

        manager.kill_game()
        self.games.pop(manager.gameid, None)

    def force_end_game(self, manager):
        for u in manager.get_online_users():
            self.exit_game(u, is_drop=True)

        self.try_remove_empty_game(manager)
        self.refresh_status()

    def start_game(self, manager):
        log.info("game started")
        stats({'event': 'start_game', 'attributes': {'gametype': manager.gamecls.__name__}})
        manager.start_game()
        self.refresh_status()

    @_command(['hang'], [])
    def quick_start_game(self, user):
        if user.state != 'hang':
            user.write(['message_err', 'cant_join_game'])
            return

        for manager in self.games.values():
            if manager.next_free_slot() is not None and manager.is_invited(user) and not manager.is_banned(user):
                self.join_game(user, manager.gameid)
                return
        else:
            user.write(['message_err', 'cant_join_game'])

    def end_game(self, manager):
        log.info("end game")
        manager.archive()

        all_dropped = not bool(manager.get_online_users())

        if not all_dropped:
            bonus = manager.get_bonus()

            for u, l in bonus.iteritems():
                u.account.add_credit(l)

        for u in manager.users:
            u.gclear()  # clear game data
            self.dropped_users.pop(u.account.userid, 0)

        manager.end_game()
        self.games.pop(manager.gameid, 0)

        if all_dropped:
            return

        new_mgr = self.create_game(None, manager.gamecls.__name__, manager.game_name, manager.invite_only)
        new_mgr.copy_invited(manager)
        manager.is_match and new_mgr.set_match(manager.match_users)

        for u in manager.users:
            self.join_game(u, new_mgr.gameid)

        new_mgr.update_game_param(manager.game_params)
        self.refresh_status()

    @_command(['inroomwait', 'ready', 'ingame', 'observing'], [])
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
            user.write(['message_err', 'not_in_a_game'])

    @_command(['hang'], [int])
    def send_gameinfo(self, user, gid):
        manager = self.games.get(gid)
        if not manager:
            return

        manager.send_gameinfo(user)

    @_command(['inroomwait', 'observing'], [int])
    def change_location(self, user, loc):
        manager = GameManager.get_by_user(user)
        if user.state == 'inroomwait':
            manager.change_location(user, loc)
            self.refresh_status()
        elif user.state == 'observing':
            self.join_game(user, manager.gameid, loc)

    @_command(['inroomwait'], [str, object])
    def set_game_param(self, user, key, value):
        if user.state != 'inroomwait':
            return

        manager = GameManager.get_by_user(user)
        manager.set_game_param(user, key, value)
        self.refresh_status()

    @_command(['inroomwait'], [str])
    def use_item(self, user, item):
        if user.state != 'inroomwait':
            return

        manager = GameManager.get_by_user(user)
        manager.use_item(user, item)

    @_command(['inroomwait', 'ready'], [int])
    def kick_user(self, user, uid):
        other = self.users.get(uid)
        if not other:
            return

        manager = GameManager.get_by_user(user)
        if manager.kick_user(user, other):
            self.exit_game(other)

    @_command(['inroomwait', 'ready', 'ingame'], [int])
    def kick_observer(self, user, uid):
        other = self.users.get(uid)
        if not other:
            return

        manager = GameManager.get_by_user(user)
        if manager.kick_observer(user, other):
            self.exit_game(other)

    @_command(['inroomwait'], [])
    def get_ready(self, user):
        manager = GameManager.get_by_user(user)
        manager.get_ready(user)
        self.refresh_status()

    @_command(['ready'], [])
    def cancel_ready(self, user):
        manager = GameManager.get_by_user(user)
        manager.cancel_ready(user)
        self.refresh_status()

    @_command(['hang'], [int])
    def observe_user(self, user, other_userid):
        other = self.users.get(other_userid, None)

        if not other:
            user.write(['message_err', 'no_such_user'])
            return

        if other.state == 'observing':
            other = other.observing

        if other.state not in ('ingame', 'inroomwait', 'ready'):
            user.write(['message_err', 'user_not_ingame'])
            return

        if user.account.userid in self.bigbrothers:
            gevent.spawn(other.write, ['system_msg', [None,
                u'管理员对你使用了强制观战，效果拔群。'
                u'强制观战功能仅用来处理纠纷，如果涉及滥用，请向 Proton 投诉。'
            ]])
            manager = GameManager.get_by_user(other)
            manager.observe_user(user, other)
            self.refresh_status()
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
                    user.write(['message_err', 'user_not_ingame'])
                else:
                    manager = GameManager.get_by_user(other)
                    manager.observe_user(user, other)
                    self.refresh_status()
            else:
                user.write(['observe_refused', other.account.username])

        worker.gr_name = 'OB:[%r] -> [%r]' % (user, other)

    @_command(['inroomwait', 'ready'], [int])
    def invite_user(self, user, other_userid):
        if user.account.userid < 0:
            gevent.spawn(user.write, ['system_msg', [None, u'毛玉不能使用邀请功能']])
            return

        other = self.users.get(other_userid, None)

        if not (other and other.state in ('hang', 'observing')):
            user.write(['message_err', 'no_such_user'])
            return

        manager = GameManager.get_by_user(user)
        manager.add_invited(other)

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

    @_command(['hang', 'inroomwait', 'ready', 'ingame', 'observing'], [unicode])
    def chat(self, user, msg):
        acc = user.account

        @gevent.spawn
        @log_failure(log)
        def worker():
            manager = GameManager.get_by_user(user)

            if msg.startswith('!!') and (options.freeplay or acc.userid in self.admins):
                self.handle_admin_cmd(user, msg[2:])
                return

            packed = (acc.username, msg)
            if user.state == 'hang':  # lobby chat
                log.info(u'(Lobby): %s' % msg)
                for u in self.users.values():
                    if u.state == 'hang':
                        u.write(['chat_msg', packed])

            elif user.state in ('inroomwait', 'ready', 'ingame', 'observing'):  # room chat
                log.info(u'(%s): %s' % (user.current_game.gameid, msg))
                ul = manager.users
                obl = BatchList()
                map(obl.__iadd__, ul.observers)
                _type = 'ob_msg' if user.state == 'observing' else 'chat_msg'
                ul.write([_type, packed])  # should be here?
                obl.write([_type, packed])

        worker.gr_name = 'Chat:%s[%s]' % (acc.username, acc.userid)

    @_command(['hang', 'inroomwait', 'ready', 'ingame', 'observing'], [unicode])
    def speaker(self, user, msg):
        @gevent.spawn
        def worker():
            if user.account.other['credits'] < 0:
                user.write(['system_msg', [None, u'您的节操掉了一地，文文不愿意帮你散播消息。']])
            else:
                Subsystem.interconnect.publish('speaker', [user.account.username, msg])

        log.info(u'Speaker: %s', msg)

    def system_msg(self, msg):
        @gevent.spawn
        def worker():
            for u in self.users.values():
                u.write(['system_msg', [None, msg]])

    def handle_admin_cmd(self, user, cmd):
        args = map(unicode, shlex.split(cmd.encode('utf-8')))
        cmd = args[0]
        args = args[1:]

        if cmd == 'stacktrace':
            manager = GameManager.get_by_user(user)
            manager.record_stacktrace()
        elif cmd == 'clearzombies':
            self.clearzombies()
        elif cmd == 'ping':
            self.ping(user)
        elif cmd == 'start_migration':
            self.start_migration()
        elif cmd == 'kick':
            uid, = args
            self.force_disconnect(int(uid))
        elif cmd == 'match':
            self.setup_match(user, *args)
        elif cmd == 'kill_game':
            gid, = args
            manager = self.games.get(int(gid))
            manager and self.force_end_game(manager)
        elif cmd == 'add_admin':
            uid, = args
            self.admins.append(int(uid))
        elif cmd == 'remove_admin':
            uid, = args
            self.admins.remove(int(uid))
        elif cmd == 'bigbrother':
            self.bigbrothers.append(user.account.userid)
        elif cmd == 'nobigbrother':
            try:
                self.bigbrothers.remove(user.account.userid)
            except Exception:
                pass
        elif cmd == 'give_item':
            from server.item import backpack
            uid, sku = args
            backpack.add(int(uid), sku)
        else:
            return

        user.write(['system_msg', [None, u'成功的执行了管理命令']])

    def force_disconnect(self, uid):
        user = self.users.get(uid)
        user and user.close()

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

    def start_migration(self):
        @gevent.spawn
        def sysmsg():
            while True:
                users = BatchList(self.users.values())
                users.write(['system_msg', [None, u'游戏已经更新，当前的游戏结束后将会被自动踢出，请更新后重新游戏']])
                gevent.sleep(30)

        @gevent.spawn
        def kick():
            gevent.sleep(30)
            while True:
                users = self.users.values()
                for u in users:
                    if u.state in ('hang', 'inroomwait', 'ready', 'connected'):
                        u.close()

                gevent.sleep(1)

    def setup_match(self, operator, name, gametype, *players):
        from thb import modes
        gid = self.new_gid()
        gamecls = modes[gametype]
        if len(players) != gamecls.n_persons:
            operator.write(['system_msg', [None, u'参赛人数不正确']])
            return

        manager = GameManager(gid, gamecls, name, False)
        pl = []
        for i in players:
            try:
                uid = int(i)
            except:
                uid = 100000

            pl.append(uid if uid < 100000 else i)

        manager.set_match(pl)
        self.games[gid] = manager
        log.info("Create game")

        @gevent.spawn
        def pull():
            while gid in self.games:
                users = self.users.values()
                for u in users:
                    if not (u.account.userid in pl or u.account.username in pl):
                        continue

                    already_in = GameManager.get_by_user(u) is manager
                    if u.state == 'hang':
                        self.join_game(u, gid)
                    elif u.state in ('observing', 'ready', 'inroomwait') and not already_in:
                        self.exit_game(u)
                        gevent.sleep(1)
                        self.join_game(u, gid)
                    elif u.state == 'ingame' and not already_in:
                        gevent.spawn(u.write, ['system_msg', [None, u'你有比赛房间，请尽快结束游戏参与比赛']])

                gevent.sleep(30)

        self.refresh_status()

        return manager

if options.gidfile and os.path.exists(options.gidfile):
    last_gid = int(open(options.gidfile, 'r').read())
else:
    last_gid = 0

Subsystem.lobby = Lobby(last_gid)


@atexit.register
def _exit_handler():
    # logout all the accounts
    # to save the credits
    for u in Subsystem.lobby.users.values():
        u.account.add_credit(['credits', 50])

    # save gameid
    fn = options.gidfile
    if fn:
        with open(fn, 'w') as f:
            f.write(str(Subsystem.lobby.current_gid + 1))
