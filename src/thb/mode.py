# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, List, TYPE_CHECKING, Type

# -- third party --
# -- own --
from game.base import Action, EventDispatcher, EventHandler, Game, Player
from utils.misc import BatchList

# -- typing --
if TYPE_CHECKING:
    from thb.cards.base import Card, Deck  # noqa: F401
    from thb.characters.base import Character  # noqa: F401
    from thb.common import PlayerRole  # noqa: F401


# -- code --
class THBEventDispatcher(EventDispatcher):
    game: 'THBattle'

    def populate_handlers(self) -> List[EventHandler]:
        from thb.actions import COMMON_EVENT_HANDLERS
        g = self.game
        ehclasses = list(COMMON_EVENT_HANDLERS) + list(g.game_ehs)
        for c in getattr(g, 'players', ()):
            ehclasses.extend(c.eventhandlers)

        return EventHandler.make_list(g, ehclasses)


class THBEventHandler(EventHandler):
    game: THBattle


class THBAction(Action):
    source: Character
    target: Character
    game: THBattle
    associated_card: Card

    def __init__(self, source: Character, target: Character):
        self.source = source
        self.target = target


class THBattle(Game[THBAction, THBEventHandler]):
    game: THBattle
    game_ehs: List[Type[THBEventHandler]]
    deck: Deck
    players: BatchList[Character]
    roles: Dict[Player, PlayerRole]
    dispatcher: THBEventDispatcher
    round: int = 0

    dispatcher_cls = THBEventDispatcher

    def find_character(g, p: Player) -> Character:
        for ch in g.players:
            if ch.get_player() is p:
                return ch

        raise IndexError('Could not find character!')
