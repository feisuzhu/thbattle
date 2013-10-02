# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
import atexit
import logging
import os
import random
import time
import gzip

# -- third party --
import gevent
from gevent import Greenlet
from gevent.event import Event
import simplejson as json
import pika

# -- own --
from network import Endpoint
from network.server import Client as ClientEndpoint, DroppedClient
from utils import BatchList, surpress_and_restart, swallow, instantiate, log_failure
from options import options
from settings import VERSION
from account import Account

# -- code --
log = logging.getLogger('GameHall')

# mute pika loggers
pika.channel.LOGGER.setLevel(logging.CRITICAL)
pika.connection.LOGGER.setLevel(logging.CRITICAL)
pika.adapters.blocking_connection.LOGGER.setLevel(logging.CRITICAL)


class Client(ClientEndpoint):
    def handle_command(self, cmd, data):
        f = getattr(self, 'command_' + str(cmd), None)
        if not f:
            log.debug('No command %s', cmd)
            self.write(['invalid_command', [cmd, data]])
            return

        for_state = getattr(f, 'for_state', None)
        if for_state and self.state not in for_state:
            log.debug('Command %s is for state %s, called in %s', cmd, for_state, self.state)
            self.write(['invalid_command', [cmd, data]])
            return

        f(data)

    def handle_drop(self):
        if self.state not in ('connected', 'hang'):
            exit_game(self, drops=True)

        if self.state != 'connected':
            user_exit(self)

    def for_state(*state):
        def register(f):
            f.for_state = state
            return f

        return register

    # --------- Handlers ---------
    @for_state('connected')
    def command_auth(self, cred):
        if self.account:
            self.write(['invalid_command', ['auth', '']])
            return

        login, password = cred
        acc = Account.authenticate(login, password)
        if acc:
            self.account = acc
            if not acc.available():
                self.write(['auth_result', 'not_available'])
                self.close()
            else:
                self.write(['auth_result', 'success'])
                self.account = acc
                new_user(self)

        else:
            self.write(['auth_result', 'invalid_credential'])

    @for_state('hang')
    def command_create_game(self, arg):
        _type, name = arg
        g = create_game(self, _type, name)
        join_game(self, g.gameid)

    @for_state('hang')
    def command_join_game(self, gameid):
        join_game(self, gameid)

    @for_state('hang')
    def command_get_hallinfo(self, _):
        send_hallinfo(self)

    @for_state('hang')
    def command_quick_start_game(self, _):
        quick_start_game(self)

    @for_state('hang')
    def command_observe_user(self, uid):
        observe_user(self, uid)

    @for_state('inroomwait', 'ready', 'ingame')
    def command_observe_grant(self, rst):
        observe_grant(self, rst)

    @for_state('hang')
    def command_query_gameinfo(self, gid):
        query_gameinfo(self, gid)

    @for_state('inroomwait')
    def command_get_ready(self, _):
        get_ready(self)

    @for_state('inroomwait', 'ready', 'ingame', 'observing')
    def command_exit_game(self, _):
        exit_game(self)

    @for_state('inroomwait', 'ready')
    def command_kick_user(self, uid):
        kick_user(self, uid)

    @for_state('inroomwait', 'ready', 'ingame')
    def command_kick_observer(self, uid):
        kick_observer(self, uid)

    @for_state('inroomwait', 'observing')
    def command_change_location(self, loc):
        change_location(self, loc)

    @for_state('ready')
    def command_cancel_ready(self, _):
        cancel_ready(self)

    def command_heartbeat(self, _):
        pass

    @for_state('hang', 'inroomwait', 'ready', 'ingame', 'observing')
    def command_chat(self, data):
        chat(self, data)

    @for_state('hang', 'inroomwait', 'ready', 'ingame', 'observing')
    def command_speaker(self, data):
        speaker(self, data)

    # --------- End handlers ---------

    del for_state


'''
User state machine:
     [Observing]     --------------<------------<-----------
          |          |                                     |
    -> [Hang] <-> [InRoomWait] <-> [Ready] -> [InGame] -->----
        |                  |         |             |
        --->[[Disconnect]]<-------------------------
'''

# should use WeakSet or WeakValueDictionary,
# but this works fine, not touching it.
games = {}  # all games
users = {}  # all users
dropped_users = {}  # passively dropped users
evt_datachange = Event()


if options.gidfile:
    try:
        with open(options.gidfile, 'r') as f:
            _curgameid = int(f.read())
    except:
        _curgameid = 0
else:
    _curgameid = 0


def new_gameid():
    global _curgameid
    _curgameid += 1
    return _curgameid


if options.interconnect:
    @instantiate
    class Interconnect(object):
        def __init__(self):
            self.conn = None
            self.chan = None
            self.connect()

        def connect(self):
            try:
                self.conn = conn = pika.BlockingConnection(
                    pika.connection.ConnectionParameters(host=options.rabbitmq_host),
                )
                self.chan = chan = conn.channel()
                chan.exchange_declare('thb_events', 'fanout')
            except:
                log.error('error connecting rabbitmq', exc_info=True)
                self.conn = self.chan = None

        def publish(self, key, body):
            try:
                self.chan.basic_publish(
                    'thb_events', '%s:%s' % (options.node, key),
                    Endpoint.encode(body),
                )
            except:
                log.error('error publishing', exc_info=True)
                swallow(self.shutdown)()
                self.connect()

        def shutdown(self):
            self.chan.close()
            self.conn.close()

    atexit.register(Interconnect.shutdown)

    class InterconnectHandler(Greenlet):
        @surpress_and_restart
        def _run(self):
            try:
                conn = chan = None
                conn = pika.BlockingConnection()
                chan = conn.channel()
                chan.exchange_declare('thb_events', 'fanout')
                queue = chan.queue_declare(
                    exclusive=True,
                    auto_delete=True,
                    arguments={'x-message-ttl': 1000},
                )
                chan.queue_bind(queue.method.queue, 'thb_events')

                for method, header, body in chan.consume(queue.method.queue):
                    chan.basic_ack(method.delivery_tag)
                    body = json.loads(body)
                    node, topic = method.routing_key.split(':')

                    if topic == 'speaker':
                        @gevent.spawn
                        @log_failure(log)
                        def speaker(body=body, node=node):
                            node = node if node != options.node else ''
                            body.insert(0, node)
                            for u in users.values():
                                # u.write(['speaker_msg', [user.account.username, msg]])
                                # u.write(['speaker_msg', ['%s(%s)' % (body[0], options.node), body[1]]])
                                u.write(['speaker_msg', body])

            finally:
                gevent.sleep(1)
                chan and swallow(chan.close)()
                conn and swallow(conn.close)()

        def __repr__(self):
            return self.__class__.__name__

    InterconnectHandler = InterconnectHandler.spawn()

else:
    @instantiate
    class Interconnect(object):
        def publish(self, key, body):
            pass


@gevent.spawn
@log_failure(log)
def gamehall_status_updator():
    last_update = time.time()
    evt = evt_datachange
    time_limit = 1
    while True:
        evt.wait()
        t = time.time()
        delta = t - last_update
        if delta > time_limit:
            last_update = t
            for u in users.values():
                if u.state == 'hang':
                    send_hallinfo(u)

            Interconnect.publish('current_users', users.values())
            Interconnect.publish('current_games', games.values())

            evt.clear()

        else:
            gevent.sleep(time_limit - delta)


@instantiate
class PlayerPlaceHolder(object):

    def __data__(self):
        return dict(
            state='left',
            account=None,
        )

    @instantiate
    class client(object):
        state = 'left'
        observers = BatchList()
        raw_write = write = lambda *a: False


def new_user(user):
    uid = user.account.userid
    user.write(['your_account', user.account])
    if uid in users:
        # squeeze the original one out
        log.info('%s has been sqeezed out' % user.account.username)
        old = users[uid]
        #if old.state not in('connected', 'hang'):
        #    exit_game(old, drops=True)
        old.write(['others_logged_in', None])
        old.close()

        user.account = old.account

    users[uid] = user
    user.state = 'hang'
    user.observing = None
    log.info(u'User %s joined, online user %d' % (user.account.username, len(users)))

    if uid in dropped_users:
        log.info(u'%s rejoining dropped game' % user.account.username)
        old = dropped_users[uid]
        assert isinstance(old, DroppedClient), 'Arghhhhh'

        g = user.current_game = old.current_game
        user.player_index = old.player_index
        user.gdhistory = old.gdhistory
        user.usergdhistory = old.usergdhistory
        user.state = 'ingame'

        for p in g.players:
            if p.client is old:
                break
        else:
            assert False, 'Oops'

        p.client = user
        p.dropped = False

        user.account = old.account

        user.write(['game_joined', g])
        user.write(['game_started', g.players_original])

        user.replay(user)

        del dropped_users[uid]

        _notify_playerchange(g)

    evt_datachange.set()
    return True


def user_exit(user):
    uid = user.account.userid
    del users[uid]
    log.info(u'User %s leaved, online user %d' % (user.account.username, len(users)))
    evt_datachange.set()


def _notify_playerchange(g):
    @gevent.spawn
    def notify_playerchage_worker():
        try:
            from network.server import Client
            s = Client.encode(['player_change', g.players])
            for cl in g.players.client:
                cl.raw_write(s)
                if cl.observers: cl.observers.raw_write(s)

        except Exception as e:
            log.warning('Exception in _notify_playerchange: %s', e.__class__.__name__)


def query_gameinfo(user, gid):
    g = games.get(gid, None)
    if g: user.write(['gameinfo', [gid, g.players]])


def _next_free_slot(game):
    try:
        return game.players.index(PlayerPlaceHolder)
    except ValueError:
        return None


def create_game(user, gametype, gamename):
    from gamepack import gamemodes
    if not gametype in gamemodes:
        user.write(['gamehall_error', 'gametype_not_exist'])
        return

    g = gamemodes[gametype]()
    g.game_started = False
    g.game_name = gamename
    g.players = BatchList([PlayerPlaceHolder] * g.n_persons)
    g.players_original = None
    g.rndseed = random.randint(1, 10 ** 20)
    g.random = random.Random(g.rndseed)
    g.banlist = defaultdict(set)
    gid = new_gameid()
    g.gameid = gid
    games[gid] = g
    log.info("create game")
    evt_datachange.set()
    return g


def _archive_game(g):
    if not options.archive_path:
        return

    data = []

    data.append('# ' + ', '.join([
        p.account.username.encode('utf-8')
        for p in g.players
    ]))

    data.append('# Ver: ' + VERSION)
    data.append('# GameId: ' + str(g.gameid))
    s, e = int(g.start_time), int(time.time())
    data.append('# Time: start = %d, end = %d, elapsed = %d' % (s, e, e - s))

    data.append(g.__class__.__name__)
    data.append(str(g.rndseed))
    data.append(json.dumps(g.usergdhistory))
    data.append(json.dumps(g.gdhistory))

    f = gzip.open(os.path.join(options.archive_path, str(g.gameid)) + '.gz', 'wb')
    f.write('\n'.join(data))
    f.close()


def get_ready(user):
    user.state = 'ready'
    g = user.current_game
    _notify_playerchange(g)
    if all(p.client.state == 'ready' for p in g.players):
        if not g.started:
            # race condition here.
            # wrap in 'if g.started' to prevent double starting.
            log.info("game starting")
            g.start()

    else:
        evt_datachange.set()


def cancel_ready(user):
    user.state = 'inroomwait'
    _notify_playerchange(user.current_game)
    evt_datachange.set()


def change_location(user, loc):
    g = user.current_game
    pl = g.players
    if (not 0 <= loc < len(g.players)) or (pl[loc] is not PlayerPlaceHolder):
        user.write(['change_loc_failed', None])
        return
    if user.state == 'observing':
        join_game(user, g.gameid, loc)
    else:
        i = pl.client.index(user)
        pl[loc], pl[i] = pl[i], pl[loc]
        _notify_playerchange(g)


def kick_user(user, uid):
    g = user.current_game
    u = users.get(uid, None)
    cl = g.players.client
    if u not in cl:
        return
    bl = g.banlist[u]
    bl.add(user)
    cl.write(['kick_request', [user, u, len(bl)]])
    if len(bl) >= len(cl)//2:
        exit_game(u)


def kick_observer(user, uid):
    g = user.current_game
    ob = users.get(uid, None)
    if not (ob and ob.state == 'observing'):
        return

    if g is not ob.current_game:
        return

    exit_game(ob)


def exit_game(user, drops=False):
    if user.state == 'observing':
        tgt = user.observing
        tgt.observers.remove(user)
        user.state = 'hang'
        user.observing = None
        user.current_game = None
        user.gclear()
        user.write(['game_left', None])

        @gevent.spawn
        def notify_observer_leave(user=user, observee=tgt):
            g = tgt.current_game
            ul = g.players.client
            info = [user.account.userid, user.account.username, observee.account.username]
            ul.write(['observer_leave', info])
            for obl in ul.observers:
                obl and obl.write(['observer_leave', info])

    elif user.state != 'hang':
        g = user.current_game
        if not drops: user.gclear()
        i = g.players.client.index(user)
        if g.game_started:
            p = g.players[i]
            log.info('player dropped')
            if g.can_leave(p):
                user.write(['game_left', None])
                p.fleed = False
            else:
                if not drops:
                    user.write(['fleed', None])
                    p.fleed = True
                else:
                    p.fleed = False

            p.client.gbreak()  # XXX: fuck I forgot why it's here. Exp: see comment on Client.gbreak

            p.dropped = True
            dummy = DroppedClient(g.players[i].client)
            if drops:
                dropped_users[p.client.account.userid] = dummy
            p.client = dummy
        else:
            log.info('player leave')
            g.players[i] = PlayerPlaceHolder
            user.write(['game_left', None])

        for ob in user.observers:
            ob.write(['game_left', None])
            ob.state = 'hang'
            ob.observing = None
        user.observers[:] = []

        user.state = 'hang'
        _notify_playerchange(g)

        for bl in g.banlist.values():
            try:
                bl.remove(user)
            except KeyError:
                pass

        if all((p is PlayerPlaceHolder or p.dropped) for p in g.players):
            if g.game_started:
                log.info('game aborted')
                _archive_game(g)
            else:
                log.info('game canceled')

            for p in g.players:
                if p is PlayerPlaceHolder: continue
                try:
                    del dropped_users[p.client.account.userid]
                except KeyError:
                    pass

            g.suicide = True  # game will kill itself in get_synctag()
            try:
                del games[g.gameid]
            except:
                pass

        evt_datachange.set()
    else:
        user.write(['gamehall_error', 'not_in_a_game'])


def join_game(user, gameid, slot=None):
    if user.state == 'hang' and gameid in games:
        g = games[gameid]
    elif user.state == 'observing':
        g = user.current_game
        g = g if g.gameid == gameid else None

    if g is not None:
        if len(g.banlist[user]) >= 3:
            user.write(['gamehall_error', 'banned'])
            return

        log.info("join game")

        if slot is None:
            slot = _next_free_slot(g)
        elif g.players[slot] is not PlayerPlaceHolder:
            slot = None

        if slot is not None:
            if user.state == 'observing':
                user.observing.observers.remove(user)
                user.observing = None

            user.state = 'inroomwait'
            user.current_game = g
            from .game_server import Player
            g.players[slot] = Player(user)
            user.write(['game_joined', g])
            _notify_playerchange(g)
            evt_datachange.set()
            return

    user.write(['gamehall_error', 'cant_join_game'])


def quick_start_game(user):
    if user.state == 'hang':
        gl = [g for g in games.values() if _next_free_slot(g) is not None]
        if gl:
            join_game(user, random.choice(gl).gameid)
            return

    user.write(['gamehall_error', 'cant_join_game'])


def _observe_user(user, observee):
    if not observee:
        user.write(['gamehall_error', 'no_such_user'])
        return

    if observee.state not in ('ingame', 'inroomwait', 'ready'):
        user.write(['gamehall_error', 'user_not_ingame'])
        return

    g = observee.current_game
    observee.observers.append(user)

    log.info("observe game")
    user.state = 'observing'
    user.current_game = g
    user.observing = observee
    user.write(['game_joined', g])
    user.gclear()  # clear stale gamedata
    #_notify_playerchange(g)
    pl = g.players if not g.players_original else g.players_original
    evt_datachange.set()

    @gevent.spawn
    def notify_observer():
        ul = g.players.client
        info = [user.account.userid, user.account.username, observee.account.username]
        ul.write(['observer_enter', info])
        for obl in ul.observers:
            obl and obl.write(['observer_enter', info])

    if g.started:
        user.write(['observe_started', [observee.account.userid, pl]])
        observee.replay(user)


observe_table = defaultdict(set)


def observe_user(user, other_userid):
    other = users.get(other_userid, None)

    if not other:
        user.write(['gamehall_error', 'no_such_user'])
        return

    if other.state not in ('ingame', 'inroomwait', 'ready'):
        user.write(['gamehall_error', 'user_not_ingame'])
        return

    observe_table[other_userid].add(user.account.userid)
    other.write(['observe_request', [user.account.userid, user.account.username]])


def observe_grant(user, rst):
    try:
        ob_id, grant = rst
    except:
        return

    l = observe_table[user.account.userid]
    if ob_id in l:
        l.remove(ob_id)
        ob = users.get(ob_id, None)
        if not (ob and ob.state == 'hang'): return
        if grant:
            _observe_user(ob, user)
        else:
            ob.write(['observe_refused', user.account.username])


def send_hallinfo(user):
    user.write(['current_games', games.values()])
    user.write(['current_users', users.values()])
    user.write(['your_account', user.account])


def start_game(g):
    log.info("game started")
    g.game_started = True
    g.players_original = BatchList(g.players)
    g.usergdhistory = ugh = []
    g.gdhistory = [list() for p in g.players]

    for i, (u, l) in enumerate(zip(g.players.client, g.gdhistory)):
        u.player_index = i
        u.usergdhistory = ugh
        u.gdhistory = l

    g.start_time = time.time()
    for u in g.players.client:
        u.write(["game_started", g.players])
        u.gclear()
        if u.observers:
            u.observers.gclear()
            u.observers.write(['observe_started', [u.account.userid, g.players]])
        u.state = 'ingame'
    evt_datachange.set()


def end_game(g):
    from .game_server import Player

    log.info("end game")
    pl = g.players

    # add credits
    t = time.time()
    percent = min(1.0, (t - g.start_time) / 1200)
    import math
    rate = math.sin(math.pi / 2 * percent)
    winners = g.winners
    bonus = g.n_persons * 5 / len(winners) if winners else 0

    _archive_game(g)

    all_dropped = all(p.dropped for p in pl)
    # TODO: likely there is something wrong, log it

    for p in pl:
        acc = p.client.account
        if not all_dropped:
            acc.add_credit('games', 1)
            if p.dropped and p.fleed:
                acc.add_credit('drops', 1)
            else:
                s = 5 + bonus if p in winners else 5
                acc.add_credit('credits', int(s * rate))

        p.client.gclear()  # clear game data

        if p.dropped:
            try:
                del dropped_users[acc.userid]
            except KeyError:
                pass

    # -----------

    for i, p in enumerate(pl):
        if p.dropped:
            pl[i] = PlayerPlaceHolder
    del games[g.gameid]
    ng = create_game(None, g.__class__.__name__, g.game_name)
    ng.players = BatchList([
        Player(p.client)
        if p is not PlayerPlaceHolder
        else PlayerPlaceHolder
        for p in pl
    ])
    for cl in pl.client:
        cl.write(['end_game', None])
        cl.write(['game_joined', ng])
        if cl.observers:
            obl = cl.observers
            obl.write(['end_game', None])
            obl.write(['game_joined', ng])
        cl.current_game = ng
        cl.state = 'inroomwait'
        for ob in cl.observers:
            ob.current_game = ng
            ob.state = 'observing'
    _notify_playerchange(ng)
    evt_datachange.set()


def chat(user, msg):
    @gevent.spawn
    @log_failure(log)
    def worker():
        packed = (user.account.username, msg)
        if user.state == 'hang':  # hall chat
            for u in users.values():
                if u.state == 'hang':
                    u.write(['chat_msg', packed])

        elif user.state in ('inroomwait', 'ready', 'ingame', 'observing'):  # room chat
            ul = user.current_game.players.client
            obl = BatchList()
            map(obl.__iadd__, ul.observers)
            _type = 'ob_msg' if user.state == 'observing' else 'chat_msg'
            ul.write([_type, packed])  # should be here?
            obl.write([_type, packed])


def speaker(user, msg):
    def worker():
        if user.account.other['credits'] < 10:
            user.write(['system_msg', [None, u'您的节操掉了一地，文文不愿意帮你散播消息。']])
        else:
            user.account.add_credit('credits', -10)
            Interconnect.publish('speaker', [user.account.username, msg])

    log.info(u'Speaker: %s', msg)
    gevent.spawn(worker)


def system_msg(msg):
    def worker():
        for u in users.values():
            u.write(['system_msg', [None, msg]])
    gevent.spawn(worker)


def admin_clearzombies():
    for i, u in users.items():
        if u.ready():
            del users[i]


@atexit.register
def _exit_handler():
    # logout all the accounts
    # to save the credits
    for u in users.values():
        u.account.add_credit('credits', 50)

    # save gameid
    fn = options.gidfile
    if fn:
        with open(fn, 'w') as f:
            f.write(str(_curgameid + 1))
