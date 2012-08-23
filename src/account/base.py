# -*- coding: utf-8 -*-

from functools import wraps

def server_side_only(f):
    @wraps(f)
    def _wrapper(*a, **k):
        from game.autoenv import Game
        if Game.CLIENT_SIDE:
            raise Exception('Server side only method!')
        return f(*a, **k)
    return _wrapper
