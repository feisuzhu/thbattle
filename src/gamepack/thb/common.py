# -*- coding: utf-8 -*-

from game.autoenv import Game, sync_primitive

def mixin_character(player, charcls):
    pcls = player.__class__
    from utils import classmix
    player.__class__ = classmix(pcls, charcls)

class CharChoice(object):
    chosen = None
    real_cls = None
    def __init__(self, char_cls, cid):
        self.char_cls = char_cls
        self.cid = cid

    def __data__(self):
        return dict(
            char_cls=self.char_cls.__name__,
            cid=self.cid,
        )

    def sync(self, data):
        from .characters import characters as chars
        from .characters.akari import Akari
        for cls in [Akari] + chars:
            if cls.__name__ == data['char_cls']:
                self.char_cls = cls
                break
        else:
            self.char_cls = None

class PlayerIdentity(object):
    def __init__(self):
        self._type = self.TYPE.HIDDEN

    def __data__(self):
        return ['identity', self.type]

    def sync(self, data):
        assert data[0] == 'identity'
        self._type = data[1]

    def is_type(self, t):
        g = Game.getgame()
        pl = g.players
        return sync_primitive(self.type == t, pl)

    def set_type(self, t):
        if Game.SERVER_SIDE:
            self._type = t

    def get_type(self):
        return self._type

    type = property(get_type, set_type)
