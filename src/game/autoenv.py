def init(place):
    global Game, EventHandler, Action, GameError
    if place == 'Server':
        from server.core import Game, EventHandler, Action, GameError
    elif place == 'Client':
        from client.core import Game, EventHandler, Action, GameError
    else:
        raise Exception('Where am I?')