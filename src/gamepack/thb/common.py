# -*- coding: utf-8 -*-

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


def init_basic_card_lists(p):
    from .cards.base import CardList
    p.cards = CardList(p, 'handcard')  # Cards in hand
    p.showncards = CardList(p, 'showncard')  # Cards which are shown to the others, treated as 'Cards in hand'
    p.equips = CardList(p, 'equips')  # Equipments
    p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
    p.special = CardList(p, 'special')  # used on special purpose
    p.droppedcards = CardList(p, 'execution')  # used cards

    p.showncardlists = [p.showncards, p.fatetell]  # cardlists should shown to others

