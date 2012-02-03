import gevent
from gevent import Greenlet
from gevent.queue import Queue
from utils import PlayerList

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

games = {} # games ready to start
games_started = {} # started games

class UserPlaceHolder(object):

    def __data__(self):
        return dict(
            id=0,
            state='n/a',
        )

    state = 'n/a'
    raw_write = write = lambda *a: False

UserPlaceHolder = UserPlaceHolder()

def new_user(user):
    #TODO: tell user to display game hall ui
    #users[id(user)] = user
    user.state = 'hang'

def _notify_playerchange(game):
    from client_endpoint import Client
    s = Client.encode(['player_change', game.players])
    for p in game.players:
        p.raw_write(s)

def _next_free_slot(game):
    try:
        return game.players.index(UserPlaceHolder)
    except IndexError as e:
        return None

def create_game(user, gametype):
    from gamepack import gamemodes
    if not gametype in gamemodes:
        user.write(['gamehall_error', 'gametype_not_exist'])
        return
    g = gamemodes[gametype]()
    g.game_started = False
    g.players = PlayerList([UserPlaceHolder] * g.n_persons)
    games[id(g)] = g
    log.info("create game")
    return g

def get_ready(user):
    user.state = 'ready'
    g = user.current_game
    _notify_playerchange(g)
    if all(p.state == 'ready' for p in g.players):
        log.info("game starting")
        g.start()

def cancel_ready(user):
    user.state = 'inroomwait'
    _notify_playerchange(user.current_game)

def exit_game(user):
    from game_server import DroppedPlayer
    if user.state != 'hang':
        g = user.current_game
        i = g.players.index(user)
        if g.game_started:
            log.info('player dropped')
            user.write(['fleed', None])
            g.players[i] = DroppedPlayer(g.players[i])
        else:
            log.info('player leave')
            g.players[i] = UserPlaceHolder
            user.write(['game_left', None])

        user.state = 'hang'
        _notify_playerchange(g)
        if all((p is UserPlaceHolder or isinstance(p, DroppedPlayer)) for p in g.players):
            if g.game_started:
                log.info('game aborted')
                del games_started[id(g)]
            else:
                log.info('game canceled')
                del games[id(g)]
            g.kill()
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
            g.players[slot] = user
            user.write(['game_joined', g])
            _notify_playerchange(g)
            return
    user.write(['gamehall_error', 'cant_join_game'])

def quick_start_game(user):
    if user.state == 'hang':
        gl = [g for g in games.values() if _next_free_slot(g) is not None]
        if gl:
            join_game(user, id(random.choice(gl)))
            return
    user.write(['gamehall_error', 'cant_join_game'])

def list_game(user):
    user.write(['current_games', games.values()])

def start_game(g):
    log.info("game started")
    g.game_started = True
    del games[id(g)]
    games_started[id(g)] = g
    for u in g.players:
        u.write(["game_started", None])
        u.state = 'ingame'
        u.__class__ = g.__class__.player_class
        u.gamedata = DataHolder()

def end_game(g):
    from game_server import DroppedPlayer
    for p in g.players:
        del p.gamedata

    log.info("end game")
    pl = g.players
    for i, p in enumerate(pl):
        if isinstance(p, DroppedPlayer):
            pl[i] = UserPlaceHolder
    del games_started[id(g)]
    ng = create_game(None, g.__class__.name)
    ng.players = pl
    for p in pl:
        p.write(['end_game', None])
        p.write(['game_joined', ng])
        p.current_game = ng
        p.state = 'inroomwait'
    _notify_playerchange(ng)
