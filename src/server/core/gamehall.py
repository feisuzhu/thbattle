import gevent
from gevent import Greenlet
from gevent.event import Event
from gevent.queue import Queue
from time import time

import logging
import random

log = logging.getLogger('GameHall')

from utils import DataHolder

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

class _GameHallStatusUpdator(Greenlet):
    def _run(self):
        last_update = time()
        timeout = None
        evt = evt_datachange
        time_limit = 1
        while True:
            flag = evt.wait()
            delta = time() - last_update
            if delta > time_limit:
                timeout = None
                last_update = time()
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
            id=0,
            state='n/a',
        )

    class client(object):
        state = 'left'
        raw_write = write = lambda *a: False
    client = client()

PlayerPlaceHolder = PlayerPlaceHolder()

def new_user(user):
    users[user.get_userid()] = user
    user.state = 'hang'
    evt_datachange.set()

def user_exit(user):
    del users[user.get_userid()]
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

def _except_logger(g):
    log.exception(g.exception)

def create_game(user, gametype, gamename):
    from gamepack import gamemodes
    from game_server import PlayerList
    if not gametype in gamemodes:
        user.write(['gamehall_error', 'gametype_not_exist'])
        return
    g = gamemodes[gametype]()
    g.link_exception(_except_logger)
    g.game_started = False
    g.game_name = gamename
    g.players = PlayerList([PlayerPlaceHolder] * g.n_persons)
    games[id(g)] = g
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

def exit_game(user):
    from game_server import Player, DroppedPlayer
    from client_endpoint import DummyClient
    if user.state != 'hang':
        g = user.current_game
        i = g.players.client.index(user)
        if g.game_started:
            log.info('player dropped')
            user.write(['fleed', None])
            p = g.players[i]
            p.client.gbreak() # XXX: fuck I forgot why it's here. Exp: see comment on Client.gbreak

            if p.__class__ is Player:
                p.__class__ = DroppedPlayer
            else:
                # HACK:it's a customized class, Player_Character or something.
                # each class like this should have only 1 instance,
                # so we can modify the class directly
                # !!classes are expensive, they need to be cached.!!
                cls = p.__class__
                bases = list(cls.__bases__)
                i = bases.index(Player)
                bases[i] = DroppedPlayer
                cls.__bases__ = tuple(bases)

            p.client = DummyClient(g.players[i].client)
        else:
            log.info('player leave')
            g.players[i] = PlayerPlaceHolder
            user.write(['game_left', None])

        user.state = 'hang'
        _notify_playerchange(g)
        if all((p is PlayerPlaceHolder or isinstance(p, DroppedPlayer)) for p in g.players):
            if g.game_started:
                log.info('game aborted')
            else:
                log.info('game canceled')
            del games[id(g)]
            g.instant_kill()
        evt_datachange.set()
    else:
        user.write(['gamehall_error', 'not_in_a_game'])

def join_game(user, gameid):
    if user.state == 'hang' and games.has_key(gameid):
        log.info("join game")
        g = games[gameid]
        slot = _next_free_slot(g)
        if slot is not None:
            user.state = 'inroomwait'
            user.current_game = g
            g.players[slot] = g.player_class(user)
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
            join_game(user, id(random.choice(gl)))
            return
    user.write(['gamehall_error', 'cant_join_game'])

def send_hallinfo(user):
    user.write(['current_games', games.values()])
    user.write(['current_players', users.values()])

def start_game(g):
    log.info("game started")
    g.game_started = True
    for u in g.players.client:
        u.write(["game_started", None])
        u.state = 'ingame'
    evt_datachange.set()

def end_game(g):
    from game_server import DroppedPlayer, PlayerList

    log.info("end game")
    pl = g.players
    for i, p in enumerate(pl):
        if isinstance(p, DroppedPlayer):
            pl[i] = PlayerPlaceHolder
    del games[id(g)]
    ng = create_game(None, g.__class__.__name__, g.game_name)
    ng.players = PlayerList(
        g.player_class(p.client)
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
    if user.state == 'hang': # hall chat
        for u in users.values():
            if u.state == 'hang':
                u.write(['chat_msg', [user.nickname, msg]])
    elif user.state in ('inroomwait', 'ready', 'ingame'): # room chat
        ul = user.current_game.players.client
        ul.write(['chat_msg', [user.nickname, msg]])

def genfunc(_type):
    def _msg(user, msg):
        for u in users.values():
            u.write([_type, [user.nickname, msg]])
    _msg.__name__ = _type
    return _msg

speaker = genfunc('speaker_msg')
system_msg = genfunc('system_msg') #FIXME!
del genfunc
