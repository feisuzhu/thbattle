# -*- coding: utf-8 -*-
import logging
log = logging.getLogger('thb.common')

from game.autoenv import Game, sync_primitive


class CharChoice(object):
    real_cls = None
    chosen = False

    def __init__(self, char_cls=None, as_akari=False):
        self.char_cls = char_cls
        self.as_akari = as_akari

    def __data__(self):
        return self.char_cls.__name__ if not self.as_akari else 'Akari'

    def sync(self, data):
        from .characters.baseclasses import Character
        self.char_cls = Character.character_classes[data]

    def conceal(self):
        self.char_cls = None
        self.real_cls = None
        self.chosen = False
        self.as_akari = False

    def __repr__(self):
        return '<Choice: {}{}>'.format(
            'None' if not self.char_cls else self.char_cls.__name__,
            '[Akari]' if self.as_akari else '',
        )


class PlayerIdentity(object):
    def __init__(self):
        self._type = self.TYPE.HIDDEN

    def __data__(self):
        return ['identity', self.type]

    def __str__(self):
        return self.TYPE.rlookup(self.type)

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
