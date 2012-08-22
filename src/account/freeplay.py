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

class Account(object):

    @classmethod
    @server_side_only
    def authenticate(cls, username, password):
        if len(username) > 0:
            acc = cls()
            acc.username = username
            acc.userid = id(acc)
            return acc

        print cls, username, password
        return False

    @server_side_only
    def logout(self):
        pass

    @classmethod
    def parse(cls, data):
        acc = cls()
        mode, acc.userid, acc.username = data
        assert mode == 'freeplay'
        return acc

    def __data__(self):
        return ['freeplay', self.userid, self.username]
