def init(place):
    global Game, EventHandler, Action, GameError, GameEnded
    if place == 'Server':
        from server.core import Game, EventHandler, Action
    elif place == 'Client':
        from client.core import Game, EventHandler, Action
    else:
        raise Exception('Where am I?')
    from game_common import GameError, GameEnded
