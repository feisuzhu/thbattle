# -*- coding: utf-8 -*-

# -- stdlib --
import zlib

# -- third party --
import msgpack

# -- own --


# -- code --
class Replay(object):
    __slots__ = (
        'version',
        'client_version',
        'game_mode',
        'game_params',
        'gamedata',
        'users',
        'me_index',
    )

    def __init__(self):
        self.version = 1
        self.client_version = None
        self.game_mode = None
        self.game_params = {}
        self.gamedata = []
        self.users = []
        self.me_index = -1

    def dumps(self):
        return zlib.compress(msgpack.packb({
            'ver':    self.version,
            'cliver': self.client_version,
            'mode':   self.game_mode,
            'params': self.game_params,
            'data':   self.gamedata,
            'users':  self.users,
            'index':  self.me_index,
        }, use_bin_type=True))

    @classmethod
    def loads(cls, replay_data):
        data = msgpack.unpackb(zlib.decompress(replay_data), encoding='utf-8')
        o = cls()
        o.version        = data['ver']
        o.client_version = data['cliver']
        o.game_mode      = data['mode']
        o.game_params    = data['params']
        o.gamedata       = data['data']
        o.users          = data['users']
        o.me_index       = data['index']

        return o
