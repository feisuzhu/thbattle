# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, List, TYPE_CHECKING, Tuple, TypeVar
import logging

# -- third party --
import gevent

# -- own --
from server.endpoint import Client
from utils.events import EventHub
from wire import msg

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Admin')
T = TypeVar('T', bound=msg.Message)
STOP = EventHub.STOP_PROPAGATION


def _need_admin(f: Callable[[Admin, Client, T], Any]) -> Callable[[Admin, Tuple[Client, T]], EventHub.StopPropagation]:
    def wrapper(self: Admin, ev: Tuple[Client, T]) -> EventHub.StopPropagation:
        core = self.core
        u, m = ev
        if core.auth.uid_of(u) not in self.admins:
            return STOP

        f(self, u, m)
        u.write(msg.SystemMsg(msg='成功的执行了管理命令'))
        return STOP

    return wrapper


class Admin(object):
    def __init__(self, core: Core):
        self.core = core

        D = core.events.client_command
        D[msg.AdminStacktrace]       += self._stacktrace
        D[msg.AdminClearZombies]     += self._clearzombies
        D[msg.AdminMigrate]          += self._migrate
        D[msg.AdminKick]             += self._kick
        D[msg.AdminKillGame]         += self._kill_game
        D[msg.AdminAdd]              += self._add
        D[msg.AdminRemove]           += self._remove
        D[msg.AdminAddBigbrother]    += self._add_bigbrother
        D[msg.AdminRemoveBigbrother] += self._remove_bigbrother

        self.admins: List[int] = [2, 109, 351, 3044, 6573, 6584, 9783]

    def __repr__(self) -> str:
        return self.__class__.__name__

    @_need_admin
    def _kick(self, c: Client, m: msg.AdminKick) -> None:
        core = self.core
        u = core.lobby.get(m.uid)
        if u: u.close()

    @_need_admin
    def _clearzombies(self, c: Client, m: msg.AdminClearZombies) -> None:
        core = self.core
        users = core.lobby.all_users()
        for u in users:
            if u.is_dead():
                log.info('Clear zombie: %r', u)
                core.events.client_dropped.emit(u)

    @_need_admin
    def _migrate(self, c: Client, m: msg.AdminMigrate) -> None:
        core = self.core

        @gevent.spawn
        def sysmsg() -> None:
            while True:
                users = core.lobby.all_users()
                users.write(msg.SystemMsg(msg='游戏已经更新，当前的游戏结束后将会被自动踢出，请更新后重新游戏'))
                gevent.sleep(30)

        @gevent.spawn
        def kick() -> None:
            gevent.sleep(30)
            while True:
                users = core.lobby.all_users()
                for u in users:
                    if core.lobby.state_of(u) in ('lobby', 'room', 'ready', 'connected'):
                        u.close()

                gevent.sleep(1)

    @_need_admin
    def _stacktrace(self, c: Client, m: msg.AdminStacktrace) -> None:
        core = self.core
        g = core.game.current(c)
        if not g:
            return

        log.info('>>>>> GAME STACKTRACE <<<<<')

        def logtraceback(f: Any) -> None:
            import traceback
            log.info('----- %r -----\n%s', gr, ''.join(traceback.format_stack(f)))

        logtraceback(g)

        for u in core.room.online_users_of(g):
            gr = u.get_greenlet()
            if gr and gr.gr_frame:
                logtraceback(gr.gr_frame)

        log.info('===========================')

    @_need_admin
    def _kill_game(self, c: Client, m: msg.AdminKillGame) -> None:
        core = self.core
        g = core.room.get(m.gid)
        if not g: return

        users = core.room.online_users_of(g)
        for u in users:
            core.room.exit_game(u)

    @_need_admin
    def _add(self, c: Client, m: msg.AdminAdd) -> None:
        self.admins.append(m.uid)

    @_need_admin
    def _remove(self, c: Client, m: msg.AdminRemove) -> None:
        try:
            self.admins.remove(m.uid)
        except Exception:
            pass

    @_need_admin
    def _add_bigbrother(self, c: Client, m: msg.AdminAddBigbrother) -> None:
        core = self.core
        core.observe.add_bigbrother(m.uid)

    @_need_admin
    def _remove_bigbrother(self, c: Client, m: msg.AdminRemoveBigbrother) -> None:
        core = self.core
        core.observe.remove_bigbrother(m.uid)
