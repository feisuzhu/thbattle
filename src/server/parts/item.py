# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Dict, List, TYPE_CHECKING, Tuple, TypedDict
import logging

# -- third party --
# -- own --
from game.base import GameItem
from server.base import Game
from server.endpoint import Client
from server.utils import command
from utils.misc import BusinessException
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.item')


class ItemAssocOnGame(TypedDict):
    items: Dict[int, List[GameItem]]


def A(self: Item, g: Game) -> ItemAssocOnGame:
    return g._[self]


class Item(object):
    def __init__(self, core: Core):
        self.core = core
        core.events.game_created += self.handle_game_created
        core.events.game_started += self.handle_game_started
        _ = core.events.client_command
        _[wire.UseItem] += self._use_item

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_game_started(self, g: Game) -> Game:
        core = self.core
        final: Dict[int, List[GameItem]] = {}

        for pid, l in A(self, g)['items'].items():
            consumed = []
            for i in l:
                try:
                    rst = core.backend.query('''
                        mutation($id: Int!, $sku: String, $r: String) {
                            item {
                                remove(player: $id, sku: $sku, reason: $r)
                            }
                        }
                    ''', id=pid, sku=i.sku, reason="Use in game %s" % core.room.gid_of(g))

                    if rst['item']['remove']:
                        consumed.append(i)
                except Exception:
                    log.exception('Error consuming item')

            final[pid] = consumed

        A(self, g)['items'] = final

        return g

    def handle_game_created(self, g: Game) -> Game:
        assoc: ItemAssocOnGame = {
            'items': defaultdict(list),
        }
        g._[self] = assoc
        return g

    def handle_game_left(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, u = ev
        core = self.core
        if not core.room.is_started(g) and not g.ended:
            A(self, g)['items'].pop(core.auth.pid_of(u), None)

        return ev

    # ----- Command -----
    @command('room')
    def _use_item(self, u: Client, ev: wire.UseItem) -> None:
        core = self.core
        g = core.game.current(u)
        assert g

        try:
            pid = core.auth.pid_of(u)
            i = GameItem.from_sku(ev.sku)
            i.should_usable(core, g, u)

            have_item = core.backend.query('''
                query($pid: Int!, $sku: String!) {
                    player(id: $id) {
                        haveItem(sku: $sku)
                    }
                }
            ''', pid=pid, sku=ev.sku)['player']['haveItem']

            if not have_item:
                from utils.misc import exceptions
                raise exceptions.ItemNotFound

            A(self, g)['items'][pid].append(i)
            u.write(wire.Info('use_item_success'))
        except BusinessException as e:
            pid = core.auth.pid_of(u)
            log.error('User %s failed to use item %s: %s', pid, ev.sku, e.name)
            u.write(wire.Error(e.snake_case))

    # ----- Methods ------
    # ----- Public Methods -----
    def items_of(self, g: Game) -> Dict[int, List[GameItem]]:
        return A(self, g)['items']

    def item_skus_of(self, g: Game) -> Dict[int, List[str]]:
        return {k: [i.sku for i in v] for k, v in self.items_of(g).items()}
