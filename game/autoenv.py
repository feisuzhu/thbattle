def init(place):
    global Game, EventHandler, Action, GameError
    if place == 'Server':
        print 'Server!'
        from server.core import Game, EventHandler, Action, GameError
    elif place == 'Client':
        print 'Client!'
        from client.core import Game, EventHandler, Action, GameError
    else:
        raise Exception('Where am I?')