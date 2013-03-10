# -*- coding: utf-8 -*-

from game.autoenv import Game, sync_primitive, EventHandler, Action, GameError, GameEnded, PlayerList, InterruptActionFlow
from .actions import PlayerTurn
from itertools import cycle
from collections import defaultdict
from utils import check, CheckFailed

#import testing

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

class GameBase(Game):
    def game_start(self):
        # game started, init state
        from cards import Card, Deck, CardList

        self.deck = Deck()
        
        for p in self.players:
            p.cards = CardList(p, 'handcard') # Cards in hand
            p.showncards = CardList(p, 'showncard') # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, 'equips') # Equipments
            p.fatetell = CardList(p, 'fatetell') # Cards in the Fatetell Zone
            p.special = CardList(p, 'special') # used on special purpose

            p.showncardlists = [p.showncards, p.fatetell]

            p.tags = defaultdict(int)
            
            p.dead = False
            p.need_shuffle = False

        self.init_identities(None)
        first_actor = self.roll_and_choose_girls(None)
        try:
            self.init_game(first_actor)
            pl = self.players.rotate_to(first_actor)
            
            for i, p in enumerate(cycle(pl)):
                if i >= 6000: break
                if not self.on_player_turn(p):
                    continue
                try:
                    self.emit_event('player_turn', p)
                    self.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass
        except GameEnded:
            pass
        else:
            #raise GameError('Game not ended')
            pass

        #assert self.winner

    def on_player_dead(self):
        pass

    def on_player_turn(self, p):
        return not p.dead
