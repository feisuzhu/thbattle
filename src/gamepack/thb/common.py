# -*- coding: utf-8 -*-
import logging
log = logging.getLogger('thb.common')

from game.autoenv import Game, sync_primitive


def mixin_character(player, char_cls):
    from utils import classmix
    pcls = player.__class__
    if hasattr(pcls, 'mixins'):
        old = player.char_cls
        player.char_cls = char_cls
        player.__class__ = classmix(player.base_cls, char_cls)
        return old
    else:
        player.base_cls = pcls
        player.char_cls = char_cls
        player.__class__ = classmix(pcls, char_cls)
        return None


class CharChoice(object):
    real_cls = None
    chosen = False

    def __init__(self, char_cls):
        self.char_cls = char_cls

    def __data__(self):
        return self.char_cls.__name__

    def sync(self, data):
        from .characters import characters as chars
        from .characters.akari import Akari

        if data == 'Akari':
            self.char_cls = Akari
            return

        self.char_cls = [cls for cls in chars if cls.__name__ == data][0]

    def __repr__(self):
        return '<Choice: {}>'.format('None' if not self.char_cls else self.char_cls.__name__)


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


def get_seed_for(p):
    if Game.SERVER_SIDE:
        seed = long(Game.getgame().random.randint(1, 10 ** 20))
    else:
        seed = 0L

    return sync_primitive(seed, p)
