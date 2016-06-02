# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from weakref import WeakSet
import gzip
import json
import logging
import os
import random
import time

# -- third party --
import gevent

# -- own --
from game.base import GameItem
from options import options
from server import item
from server.core.endpoint import Client, DroppedClient, NPCClient
from server.subsystem import Subsystem
from settings import VERSION
from utils import BatchList, BusinessException, instantiate
from utils.misc import exceptions, throttle


# -- code --
log = logging.getLogger('server.core.game_manager')


@instantiate
class ClientPlaceHolder(object):
    state     = 'left'
    account   = None
    observers = BatchList()
    raw_write = write = lambda *a: False

    def __data__(self):
        return (None, None, 'left')


class GameManager(object):

    def __init__(self, gid, gamecls, name, invite_only):
        g = gamecls()

        self.game         = g
        self.users        = BatchList([ClientPlaceHolder] * g.n_persons)
        self.game_started = False
        self.game_name    = name
        self.banlist      = defaultdict(set)
        self.ob_banlist   = defaultdict(set)
        self.gameid       = gid
        self.gamecls      = gamecls
        self.game_items   = defaultdict(set)  # userid -> {'item:meh', ...}
        self.game_params  = {k: v[0] for k, v in gamecls.params_def.items()}
        self.is_match     = False
        self.match_users  = []
        self.invite_only  = invite_only
        self.invite_list  = set()

        g.gameid    = gid
        g._manager  = self
        g.rndseed   = random.getrandbits(63)
        g.random    = random.Random(g.rndseed)
        g.players   = BatchList()
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

    @classmethod
    def get_by_game(cls, g):
        '''
        Get GameManager object for game.

        :rtype: GameManager
        '''

        return g._manager

    def send_gameinfo(self, user):
        g = self.game
        user.write(['gameinfo', [g.gameid, g.players]])

    def set_match(self, match_users):
        self.is_match = True
        self.match_users = match_users

        gevent.spawn(lambda: [gevent.sleep(1), Subsystem.interconnect.publish(
            'speaker', [u'文文', u'“%s”房间已经建立，请相关玩家就位！' % self.game_name]
        )])

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
        game_items = {k: list(v) for k, v in self.game_items.items()}
        data.append(json.dumps(game_items))
        data.append(str(g.rndseed))
        data.append(json.dumps(self.usergdhistory))
        data.append(json.dumps(self.gdhistory))

        f = gzip.open(os.path.join(options.archive_path, '%s-%s.gz' % (options.node, str(self.gameid))), 'wb')
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
        self.game_items = defaultdict(set)

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

        s = Client.encode(['kick_request', [user, other, len(bl)]])
        for cl in self.users:
            cl.raw_write(s)
            cl.observers and cl.observers.raw_write(s)

        return len(bl) >= len(self.users) // 2

    def kick_observer(self, user, other):
        if user not in self.users:
            return False

        if GameManager.get_by_user(other) is not self:
            return False

        if other.state != 'observing':
            return False

        bl = self.ob_banlist[other]
        bl.add(user)

        s = Client.encode(['ob_kick_request', [user, other, len(bl)]])
        for cl in self.users:
            cl.raw_write(s)
            cl.observers and cl.observers.raw_write(s)

        return len(bl) >= len(self.users) // 2

    def observe_leave(self, user, no_move=False):
        assert user.state == 'observing'

        tgt = user.observing
        tgt.observers.remove(user)
        try:
            del self.ob_banlist[user]
        except KeyError:
            pass
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
            user.write(['observe_started', [
                self.game_params,
                self.consumed_game_items,
                observee.account.userid,
                self.build_initial_players(),
            ]])
            self.replay(user, observee)
        else:
            self.notify_playerchange()

    def is_banned(self, user):
        if self.is_match:
            return not (user.account.userid in self.match_users or user.account.username in self.match_users)

        return len(self.banlist[user]) >= max(self.game.n_persons // 2, 1)

    def is_invited(self, user):
        return not self.invite_only or user.account.userid in self.invite_list

    def add_invited(self, user):
        self.invite_list.add(user.account.userid)

    def copy_invited(self, mgr):
        self.invite_list = set(mgr.invite_list)

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
        self._consume_items()
        g = self.game
        assert ClientPlaceHolder not in self.users
        assert all([u.state == 'ready' for u in self.users])

        if self.is_match:
            gevent.spawn(lambda: Subsystem.interconnect.publish(
                'speaker', [u'文文', u'“%s”开始了！参与玩家：%s' % (
                    self.game_name,
                    u'，'.join(self.users.account.username)
                )]
            ))

        self.game_started = True

        g.players = self.build_initial_players()

        self.usergdhistory = []
        self.gdhistory     = [list() for p in self.users]

        self.start_time = time.time()
        for u in self.users:
            u.write(["game_started", [self.game_params, self.consumed_game_items, g.players]])
            u.gclear()
            if u.observers:
                u.observers.gclear()
                u.observers.write(['observe_started', [self.game_params, self.consumed_game_items, u.account.userid, g.players]])
            u.state = 'ingame'

    def _consume_items(self):
        final = {}
        for uid, l in self.game_items.items():
            consumed = []
            for i in l:
                try:
                    item.backpack.consume(uid, i)
                    consumed.append(i)
                except exceptions.ItemNotFound:
                    pass

            final[uid] = consumed

        self.consumed_game_items = final

    def use_item(self, user, sku):
        try:
            uid = user.account.userid
            item.backpack.should_have(uid, sku)
            i = GameItem.from_sku(sku)
            i.should_usable_in_game(uid, self)
            self.game_items[uid].add(sku)
            user.write(['message_info', 'use_item_success'])
        except BusinessException as e:
            user.write(['message_err', e.snake_case])

    def clear_item(self, user):
        self.game_items[user.userid].clear()

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
        new.write(['game_started', [self.game_params, self.consumed_game_items, players]])

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
            can_leave = g.can_leave(p)

            if can_leave:
                user.write(['game_left', None])
                p.set_fleed(False)
            else:
                p.set_dropped()
                if not is_drop:
                    user.write(['fleed', None])
                    p.set_fleed(True)
                else:
                    p.set_fleed(False)

            p.client.gbreak()  # XXX: fuck I forgot why it's here. Exp: see comment on Client.gbreak

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

        self.game_items.pop(user.account.userid, 0)

        return rst

    def end_game(self):
        if self.is_match and not self.game.suicide:
            gevent.spawn(lambda: Subsystem.interconnect.publish(
                'speaker', [u'文文', u'“%s”结束了！获胜玩家：%s' % (
                    self.game_name,
                    u'，'.join(BatchList(self.game.winners).account.username)
                )]
            ))

        for u in self.users:
            u.write(['end_game', None])
            u.observers and u.observers.write(['end_game', None])
            u.state = 'hang'

    def get_online_users(self):
        return [p for p in self.users if (p is not ClientPlaceHolder and not isinstance(p, DroppedClient))]

    def kill_game(self):
        if self.is_match and self.game.started:
            gevent.spawn(lambda: Subsystem.interconnect.publish(
                'speaker', [u'文文', u'“%s”意外终止了！' % self.game_name]
            ))

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

        rst = {}

        for p in g.players:
            u = p.client
            rst[u] = []

            if isinstance(u, NPCClient):
                continue

            rst[u].append(('games', 1))
            if p.dropped or p.fleed:
                if not options.no_counting_flee:
                    rst[u].append(('drops', 1))
            else:
                s = 5 + bonus if p in winners else 5
                rst[u].append(('jiecao', int(s * rate * options.credit_multiplier)))

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
