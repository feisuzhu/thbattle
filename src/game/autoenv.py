def init(place):
    if place == 'Server':
        from server.core import Game, EventHandler, Action, PlayerList
    elif place == 'Client':
        from client.core import Game, EventHandler, Action, PlayerList
    else:
        raise Exception('Where am I?')
    from game_common import GameError, GameEnded, sync_primitive, InterruptActionFlow
    globals().update(locals())
