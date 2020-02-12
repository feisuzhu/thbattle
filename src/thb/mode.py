# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, List, Sequence, TYPE_CHECKING, Type

# -- third party --
# -- own --
from game.base import Action, EventDispatcher, EventHandler, Game, Player
from utils.misc import BatchList

# -- typing --
if TYPE_CHECKING:
    from thb.cards.base import Deck  # noqa: F401
    from thb.characters.base import Character  # noqa: F401
    from thb.common import PlayerRole  # noqa: F401


# -- code --
class THBEventDispatcher(EventDispatcher):
    game: 'THBattle'

    def populate_handlers(self) -> Sequence['THBEventHandler']:
        from thb.actions import COMMON_EVENT_HANDLERS
        g = self.game
        ehclasses = list(COMMON_EVENT_HANDLERS) + list(g.game_ehs)
        for c in getattr(g, 'players', ()):
            ehclasses.extend(c.eventhandlers)

        return EventHandler.make_list(g, ehclasses)


class THBEventHandler(EventHandler):
    game: THBattle


class THBattle(Game):
    game: THBattle
    game_ehs: List[Type[THBEventHandler]]
    deck: Deck
    players: BatchList[Character]
    roles: Dict[Player, PlayerRole]
    dispatcher: THBEventDispatcher

    dispatcher_cls = THBEventDispatcher

    def find_character(g, p: Player) -> Character:
        for ch in g.players:
            if ch.player is p:
                return ch

        raise Exception('Could not find character!')


class THBAction(Action):
    source: 'Character'
    target: 'Character'
    game: THBattle

    def __init__(self, source: Character, target: Character):
        self.source = source
        self.target = target


class THBPlayerAction(Action):
    source: Player
    target: Player
    game: THBattle

    def __init__(self, source: Player, target: Player):
        self.source = source
        self.target = target
