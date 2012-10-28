# -*- coding: utf-8 -*-

import gevent
from gevent import Greenlet
from gevent.event import Event
from gevent.queue import Queue
from time import time
from collections import defaultdict

import logging
import random

log = logging.getLogger('GameHall')

from utils import DataHolder, classmix, BatchList

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
games = {} # all games
users = {} # all users
evt_datachange = Event()

_curgameid = 0
def new_gameid():
    global _curgameid
    _curgameid += 1
    return _curgameid

class _GameHallStatusUpdator(Greenlet):
    def _run(self):
        last_update = time()
        timeout = None
        evt = evt_datachange
        time_limit = 1
        while True:
            flag = evt.wait()
            t = time()
            delta = t - last_update
            if delta > time_limit:
                timeout = None
                last_update = t
                for u in users.values():
                    if u.state == 'hang':
                        send_hallinfo(u)
                evt.clear()
            else:
                gevent.sleep(time_limit - delta)

_GameHallStatusUpdator.spawn()

class PlayerPlaceHolder(object):

    def __data__(self):
        return dict(
            state='left',
            account=None,
        )

    class client(object):
        state = 'left'
        observers = BatchList()
        raw_write = write = lambda *a: False
    client = client()

PlayerPlaceHolder = PlayerPlaceHolder()

def new_user(user):
    uid = user.account.userid
    if uid in users:
        return False
    users[uid] = user
    user.state = 'hang'
    user.observing = None
    log.info(u'User %s joined, online user %d' % (user.account.username, len(users)))
    evt_datachange.set()
    return True

def user_exit(user):
    uid = user.account.userid
    user.account.logout()
    del users[uid]
    log.info(u'User %s leaved, online user %d' % (user.account.username, len(users)))
    evt_datachange.set()

def _notify_playerchange(game):
    from client_endpoint import Client
    s = Client.encode(['player_change', game.players])
    for cl in game.players.client:
        cl.raw_write(s)
        if cl.observers: cl.observers.raw_write(s)

def query_gameinfo(user, gid):
    g = games.get(gid, None)
    if g: user.write(['gameinfo', [gid, g.players]])

def _next_free_slot(game):
    try:
        return game.players.index(PlayerPlaceHolder)
    except ValueError as e:
        return None

def create_game(user, gametype, gamename):
    from gamepack import gamemodes
    from game_server import PlayerList
    if not gametype in gamemodes:
        user.write(['gamehall_error', 'gametype_not_exist'])
        return
    g = gamemodes[gametype]()
    g.game_started = False
    g.game_name = gamename
    g.players = PlayerList([PlayerPlaceHolder] * g.n_persons)
    g.players_original = None
    g.banlist = defaultdict(set)
    gid = new_gameid()
    g.gameid = gid
    games[gid] = g
    log.info("create game")
    evt_datachange.set()
    return g

def get_ready(user):
    user.state = 'ready'
    g = user.current_game
    _notify_playerchange(g)
    if all(p.client.state == 'ready' for p in g.players):
        log.info("game starting")
        g.start()

def cancel_ready(user):
    user.state = 'inroomwait'
    _notify_playerchange(user.current_game)

def change_location(user, loc):
    g = user.current_game
    pl = g.players
    if (not 0 <= loc < len(g.players)) or (pl[loc] is not PlayerPlaceHolder):
        user.write(['change_loc_failed', None])
        return
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

def exit_game(user):
    from .game_server import Player, DroppedPlayer
    from client_endpoint import DummyClient

    if user.state == 'observing':
        tgt = user.observing
        tgt.observers.remove(user)
        user.state = 'hang'
        user.observing = None
        user.gclear()
        user.write(['game_left', None])

    elif user.state != 'hang':
        g = user.current_game
        user.gclear()
        i = g.players.client.index(user)
        if g.game_started:
            p = g.players[i]
            log.info('player dropped')
            if g.can_leave(p):
                user.write(['game_left', None])
                p.fleed = False
            else:
                user.write(['fleed', None])
                p.fleed = True
                user.account.other['games'] += 1
                user.account.other['drops'] += 1
            p.client.gbreak() # XXX: fuck I forgot why it's here. Exp: see comment on Client.gbreak

            if p.__class__ is Player:
                p.__class__ = DroppedPlayer
            else:
                # It's a dynamic created class, Mixed(Player, Character) or something.
                cls = p.__class__
                bases = list(cls.__bases__)
                bases[bases.index(Player)] = DroppedPlayer
                p.__class__ = classmix(*bases)

            p.client = DummyClient(g.players[i].client)
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

        if all((p is PlayerPlaceHolder or isinstance(p, DroppedPlayer)) for p in g.players):
            if g.game_started:
                log.info('game aborted')
            else:
                log.info('game canceled')
            del games[g.gameid]
            g.instant_kill()
        evt_datachange.set()
    else:
        user.write(['gamehall_error', 'not_in_a_game'])

def join_game(user, gameid):
    if user.state == 'hang' and games.has_key(gameid):
        g = games[gameid]
        if len(g.banlist[user]) >= 3:
            user.write(['gamehall_error', 'banned'])
            return

        log.info("join game")
        slot = _next_free_slot(g)
        if slot is not None:
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

def _observe_user(user, other):
    if not other:
        user.write(['gamehall_error', 'no_such_user'])
        return

    if other.state not in ('ingame', 'inroomwait', 'ready'):
        user.write(['gamehall_error', 'user_not_ingame'])
        return

    g = other.current_game
    other.observers.append(user)

    log.info("observe game")
    user.state = 'observing'
    user.current_game = g
    user.observing = other
    user.write(['game_joined', g])
    user.gclear() # clear stale gamedata
    #_notify_playerchange(g)
    pl = g.players if not g.players_original else g.players_original
    evt_datachange.set()

    if g.started:
        user.write(['observe_started', [other.account.userid, pl]])
        other.replay(user)

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
    g.start_time = time()
    for u in g.players.client:
        u.write(["game_started", None])
        u.gclear()
        if u.observers:
            u.observers.gclear()
            u.observers.write(['observe_started', [u.account.userid, g.players]])
        u.state = 'ingame'
    evt_datachange.set()

def end_game(g):
    from .game_server import Player, DroppedPlayer, PlayerList

    log.info("end game")
    pl = g.players

    # add credits
    t = time()
    percent = min(1.0, (t-g.start_time)/1200)
    import math
    rate = math.sin(math.pi/2*percent)
    winners = g.winners
    bonus = g.n_persons * 5 / len(winners) if winners else 0
    for p in pl:
        p.client.gclear() # clear game data
        if not (p.dropped and p.fleed):
            s = 5 + bonus if p in winners else 5
            p.client.account.other['credits'] += int(s * rate)
            p.client.account.other['games'] += 1
    # -----------

    for i, p in enumerate(pl):
        if isinstance(p, DroppedPlayer):
            pl[i] = PlayerPlaceHolder
    del games[g.gameid]
    ng = create_game(None, g.__class__.__name__, g.game_name)
    ng.players = PlayerList(
        Player(p.client)
        if p is not PlayerPlaceHolder
        else PlayerPlaceHolder
        for p in pl
    )
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
    def worker():
        if user.state == 'hang': # hall chat
            for u in users.values():
                if u.state == 'hang':
                    u.write(['chat_msg', [user.account.username, msg]])
        elif user.state in ('inroomwait', 'ready', 'ingame', 'observing'): # room chat
            ul = user.current_game.players.client
            obl = BatchList()
            map(obl.__iadd__, ul.observers)
            if user.state == 'observing':
                ul.write(['ob_msg', [user.account.username, msg]]) # should be here?
                obl.write(['ob_msg', [user.account.username, msg]])
            else:
                ul.write(['chat_msg', [user.account.username, msg]])
                obl.write(['chat_msg', [user.account.username, msg]])
    gevent.spawn(worker)

def speaker(user, msg):
    def worker():
        if user.account.other['credits'] < 3:
            user.write(['system_msg', [None, u'您的节操掉了一地，文文不愿意帮你散播消息。']])
        else:
            user.account.other['credits'] -= 3
            for u in users.values():
                u.write(['speaker_msg', [user.account.username, msg]])
    gevent.spawn(worker)

def system_msg(msg):
    def worker():
        for u in users.values():
            u.write(['system_msg', [None, msg]])
    gevent.spawn(worker)

import atexit

@atexit.register
def _exit_handler():
    # logout all the accounts
    # to save the credits
    for u in users.values():
        u.account.logout()
