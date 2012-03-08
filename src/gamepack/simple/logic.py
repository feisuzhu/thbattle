from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList
from actions import *
from itertools import cycle
import random

import logging
log = logging.getLogger('SimpleGame')

def mixin_character(player, charcls):
    pcls = player.__class__
    clsn1 = pcls.__name__
    clsn2 = charcls.__name__
    new_cls = type('%s_%s' % (clsn1, clsn2), (pcls, charcls), {})
    player.__class__ = new_cls

class SimpleGame(Game):
    name = 'Simple Game'
    n_persons = 2

    # -----BEGIN PLAYER STAGES-----
    NORMAL = 'NORMAL'
    DRAWCARD_STAGE = 'DRAWCARD_STAGE'
    ACTION_STAGE = 'ACTION_STAGE'
    DROPCARD_STAGE = 'DROPCARD_STAGE'
    # -----END PLAYER STAGES-----

    if Game.CLIENT_SIDE:
        # not loading these things on server
        # FIXME: should it be here?
        from ui import SimpleGameUI as ui_class

    def game_start(self):
        # game started, init state
        from cards import Card, Deck

        for cls in action_eventhandlers:
            self.event_handlers.append(cls())

        from characters import characters as chars
        for i, p in enumerate(self.players):
            mixin_character(p, chars[i])
            for cls in p.eventhandlers_required:
                self.event_handlers.append(cls())
            p.cards = []
            p.life = p.maxlife
            p.dead = False
            p.stage = self.NORMAL

        self.deck = Deck()

        self.emit_event('simplegame_begin', None)

        try:
            for p in self.players:
                self.process_action(DrawCards(p, amount=4))

            for p in cycle(self.players):
                if not p.dead:
                    self.emit_event('player_turn', p)
                    self.process_action(DrawCardStage(target=p))
                    self.process_action(ActionStage(target=p))
                    self.process_action(DropCardStage(target=p))
        except GameEnded:
            pass

    def game_ended(self):
        return all(p.dead or p.dropped for p in self.players)
