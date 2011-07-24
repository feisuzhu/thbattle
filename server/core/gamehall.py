import gevent
from gevent import Greenlet
from gevent.queue import Queue
from gamepack import gamemodes
from server.core import Client, User, Player, DroppedPlayer
import logging
import random

log = logging.getLogger('GameHall')

class DataHolder(object):
    def __data__(self):
        return self.__dict__

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

def new_user(user):
    #TODO: tell user to display game hall ui
    #users[id(user)] = user
    user.state = 'hang'

def _notify_playerchange(game):
    s = Client.encode(['player_change', game.players])
    for p in game.players:
        p.raw_write(s)
    
def _next_free_slot(game):
    l = [i for i in xrange(game.n_persons)]
    for p in game.players:
        del l[l.index(p.halldata.slot)]
    return l[0]

def create_game(user, gametype):
    if not gametype in gamemodes:
        user.write(['error', 'gametype_not_exist'])
        return
    g = gamemodes[gametype]()
    g.game_started = False
    games[id(g)] = g
    log.debug("create game")
    return g

def get_ready(user):
    gd = user.halldata 
    user.state = 'ready'
    g = user.current_game
    _notify_playerchange(g)
    if len(g.players) == g.n_persons and reduce(lambda r, p: r or p.state == 'ready', g.players, True):
        log.debug("game started")
        g.game_started = True
        del games[id(g)]
        games_started[id(g)] = g
        for u in g.players:
            u.write(["game_started"])
            u.state = 'ingame'
        g.start()
        
def cancel_ready(user):
    gd = user.halldata
    user.state = 'inroomwait'
    _notify_playerchange(user.current_game)

def exit_game(user):
    if hasattr(user, 'current_game'):
        g = user.current_game
        i = g.players.index(user)
        if g.game_started:
            log.debug('player dropped')
            g.players[i].halldata.dropped = True
            user.state = 'hang'
        else:
            log.debug('player leave')
            del g.players[i]
        
        _notify_playerchange(g)
        if not len(g.players):
            log.debug('game canceled')
            del games[id(g)]

def join_game(user, gameid):
    if user.state == 'hang' and games.has_key(gameid):
        log.debug("join game")
        g = games[gameid]
        if not len(g.players) >= g.n_persons:
            user.state = 'inroomwait'
            user.halldata = DataHolder()
            gd = user.halldata
            gd.slot = _next_free_slot(g)
            gd.dropped = False
            gd.managed = False
            user.current_game = g
            g.players.append(user)
            user.write(['game_joined', g])
            _notify_playerchange(g)
            return
    user.write(['cant_join_game'])

def quick_start_game(user):
    if user.state == 'hang':
        gl = [g for g in games.values() if len(g.players) < g.n_persons]
        if gl:
            join_game(user, id(random.choice(gl)))
            return
    user.write(['cant_join_game'])

def list_game(user):
    user.write(games.values())

def end_game(g):
    log.debug("end game")
    pl = [p for p in g.players if not isinstance(p, DroppedPlayer)]
    del games_started[id(g)]
    ng = create_game(None, g.__class__.name)
    ng.players = pl
    for p in pl:
        p.write(['end_game'])
        p.write(['game_joined', ng])
        p.current_game = ng
        p.state = 'inroomwait'
    _notify_playerchange(g)
        

