# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, List, Type
import logging

# -- third party --
# -- own --
from game.base import BootstrapAction, GameEnded, Player, sync_primitive
from thb.common import roll
from thb.item import GameItem
from thb.mode import THBattle
from utils.misc import BatchList
from thb.mode import THBEventHandler


# -- code --
log = logging.getLogger('THBattleUnit')


class THBattleUTBootstrap(BootstrapAction):
    game: THBattle

    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        self.source = self.target = None
        self.params = params
        self.items = items
        self.players = players

    def apply_action(self) -> bool:
        pl = self.players
        g = self.game
        items = self.items
        _ = roll(g, pl, items)
        sync_primitive(1, pl)
        sync_primitive(2, pl)
        sync_primitive(3, pl)
        sync_primitive(4, pl)
        sync_primitive(5, pl)
        sync_primitive(6, pl)
        raise GameEnded(self.players)


class THBattleDummy1(THBattle):
    n_persons  = 1
    game_ehs: List[Type[THBEventHandler]] = []
    bootstrap  = THBattleUTBootstrap

    def can_leave(g: THBattle, p: Player) -> bool:
        return False


class THBattleDummy2(THBattle):
    n_persons  = 2
    game_ehs: List[Type[THBEventHandler]] = []
    bootstrap  = THBattleUTBootstrap

    def can_leave(g: THBattle, p: Player) -> bool:
        return False


class THBattleDummy3(THBattle):
    n_persons  = 3
    game_ehs: List[Type[THBEventHandler]] = []
    bootstrap  = THBattleUTBootstrap

    def can_leave(g: THBattle, p: Player) -> bool:
        return False


class THBattleDummy4(THBattle):
    n_persons  = 4
    game_ehs: List[Type[THBEventHandler]] = []
    bootstrap  = THBattleUTBootstrap

    def can_leave(g: THBattle, p: Player) -> bool:
        return False


class THBattleUTCrashBootstrap(BootstrapAction):

    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        pass

    def apply_action(self):
        raise Exception("Deliberate crash")


class THBattleCrash(THBattle):
    n_persons  = 1
    game_ehs: List[Type[THBEventHandler]] = []
    bootstrap  = THBattleUTCrashBootstrap

    def can_leave(g: THBattle, p: Player) -> bool:
        return False


class THBattleUTHaltBootstrap(BootstrapAction):

    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        pass

    def apply_action(self):
        g = self.game
        g.core.runner.sleep(10000000)  # type: ignore
        return True


class THBattleHalt(THBattle):
    n_persons  = 1
    game_ehs: List[Type[THBEventHandler]] = []
    bootstrap  = THBattleUTHaltBootstrap

    def can_leave(g: THBattle, p: Player) -> bool:
        return False


def inject():
    import thb
    thb.modes.update({cls.__name__: cls for cls in [
        THBattleDummy1,
        THBattleDummy2,
        THBattleDummy3,
        THBattleDummy4,
        THBattleCrash,
        THBattleHalt,
    ]})
