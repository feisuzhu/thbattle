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

from utils import DataHolder, classmix

'''
User state machine:
                       --------------<------------<-----------
                       |                                     |
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
        raw_write = write = lambda *a: False
    client = client()

PlayerPlaceHolder = PlayerPlaceHolder()

def new_user(user):
    uid = user.account.userid
    if uid in users:
        return False
    users[uid] = user
    user.state = 'hang'
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
    for p in game.players:
        p.client.raw_write(s)

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
    if user.state != 'hang':
        g = user.current_game
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
            user.gclear() # clear stale gamedata
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

def send_hallinfo(user):
    user.write(['current_games', games.values()])
    user.write(['current_users', users.values()])
    user.write(['your_account', user.account])

def start_game(g):
    log.info("game started")
    g.game_started = True
    g.start_time = time()
    for u in g.players.client:
        u.write(["game_started", None])
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
    bonus = g.n_persons * 5 / len(winners)
    for p in pl:
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
        cl.current_game = ng
        cl.state = 'inroomwait'
    _notify_playerchange(ng)
    evt_datachange.set()

def chat(user, msg):
    def worker():
        if user.state == 'hang': # hall chat
            for u in users.values():
                if u.state == 'hang':
                    u.write(['chat_msg', [user.account.username, msg]])
        elif user.state in ('inroomwait', 'ready', 'ingame'): # room chat
            ul = user.current_game.players.client
            ul.write(['chat_msg', [user.account.username, msg]])
    gevent.spawn(worker)

def speaker(user, msg):
    def worker():
        if user.account.other['credits'] < 3:
            user.write(['system_msg', [None, u'您的节操不足，文文不愿意帮你散播消息。']])
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
