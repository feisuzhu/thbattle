# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import OrderedDict
from copy import copy
from typing import Any, Callable, Dict, List, Optional, Sequence, TYPE_CHECKING, Tuple, cast
import logging

# -- third party --
from gevent import Greenlet, GreenletExit, iwait
from gevent.pool import Group as GreenletGroup
import gevent

# -- own --
from .endpoint import Client
from endpoint import EndpointDied
from game.base import BootstrapAction, GameEnded, GameItem, InputTransaction, Inputlet, Player
from game.base import TimeLimitExceeded
from utils.misc import BatchList, log_failure
import game.base


# -- code --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Game_Server')


class InputWaiter(Greenlet):
    def __init__(self, game: Game, player: HumanPlayer, tag: str):
        Greenlet.__init__(self)
        self.game = game
        self.player = player
        self.tag = tag

    def _run(self) -> Optional[Tuple[str, Any]]:
        p, t = self.player, self.tag
        g = self.game
        core = g.core
        try:
            # should be [tag, <Data for Inputlet.parse>]
            # tag likes 'I?:ChooseOption:2345'
            tag, rst = core.game.gamedata_of(g, p.client).gexpect(t)
            return rst
        except EndpointDied:
            return None

    def __repr__(self) -> str:
        return '<InputWaiter: p = %s, tag = %s>' % (self.player, self.tag)


class InputWaiterGroup(GreenletGroup):
    greenlet_class = InputWaiter


def user_input(players: Sequence[Any], inputlet: Inputlet, timeout: int = 25, type: str = 'single', trans: Optional[InputTransaction] = None) -> Any:
    '''
    Type can be 'single', 'all' or 'any'
    '''

    if not trans:
        with InputTransaction(inputlet.tag(), players) as trans:
            return user_input(players, inputlet, timeout, type, trans)

    assert players
    assert type in ('single', 'all', 'any')
    assert not type == 'single' or len(players) == 1

    timeout = max(0, timeout)

    inputlet.timeout = timeout
    g = cast(Game, trans.game)

    players = list(players)

    t = {'single': '', 'all': '&', 'any': '|'}[type]
    tag = 'I{0}:{1}:'.format(t, inputlet.tag())

    ilets = {p: copy(inputlet) for p in players}
    for p in players:
        ilets[p].actor = p

    results = {p: None for p in players}
    synctags = {p: g.get_synctag() for p in players}

    orig_players = players[:]
    waiters = InputWaiterGroup()

    try:
        inputany_player = None

        for p in players:
            if isinstance(p, NPCPlayer):
                ilet = ilets[p]
                p.handle_user_input(trans, ilet)
                waiters.add(gevent.spawn(lambda v: v, ilet.data()))
            else:
                t = tag + str(synctags[p])
                waiters.spawn(g, p, t)

        for p in players:
            g.emit_event('user_input_start', (trans, ilets[p]))

        bottom_halves: Any = []  # FIXME: proper typing

        def flush() -> None:
            core = g.core
            for t, data, trans, my, rst in bottom_halves:
                # for u in g.players.client:
                for u in core.room.users_of(g):
                    core.game.write(g, u, t, data)

                g.emit_event('user_input_finish', (trans, my, rst))

            bottom_halves[:] = []

        for w in iwait(waiters, timeout=timeout + 5):
            try:
                rst = w.get()
                p, data = w.player, rst
            except Exception:
                p, data = w.player, None

            my = ilets[p]

            try:
                rst = my.parse(data)
            except Exception:
                log.exception('user_input: exception in .process()')
                # ----- FOR DEBUG -----
                if g.IS_DEBUG:
                    raise
                # ----- END FOR DEBUG -----
                rst = None

            rst = my.post_process(p, rst)

            bottom_halves.append((
                'R{}{}'.format(tag, synctags[p]), data, trans, my, rst
            ))

            players.remove(p)
            results[p] = rst

            if type != 'any':
                flush()

            if type == 'any' and rst is not None:
                inputany_player = p
                break

    except TimeLimitExceeded:
        pass

    finally:
        waiters.kill()

    # flush bottom halves
    flush()

    # timed-out players
    for p in players:
        my = ilets[p]
        rst = my.parse(None)
        rst = my.post_process(p, rst)
        results[p] = rst
        g.emit_event('user_input_finish', (trans, my, rst))
        core = g.core
        t = 'R{}{}'.format(tag, synctags[p])
        # for u in g.players.client:
        for u in core.room.users_of(g):
            core.game.write(g, u, t, None)

    if type == 'single':
        return results[orig_players[0]]

    elif type == 'any':
        if not inputany_player:
            return None, None

        return inputany_player, results[inputany_player]

    elif type == 'all':
        return OrderedDict([(p, results[p]) for p in orig_players])

    assert False, 'WTF?!'


class HaltOnStart(BootstrapAction):
    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        self.params  = params
        self.items   = items
        self.players = players

    def apply_action(self) -> bool:
        g = self.game
        assert isinstance(g, Game)
        core = g.core
        core.game.set_bootstrap_action(g, self)
        g.pause(99999999)
        return True


class Game(game.base.Game):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''

    CLIENT = False
    SERVER = True

    core: Core

    def __init__(self, core: Core):
        self.core = core
        super().__init__()

    @log_failure(log)
    def run(g) -> None:
        g.synctag = 0

        core = g.core

        core.events.game_started.emit(g)

        params = core.game.params_of(g)
        players = core.game.players_of(g)

        m: Dict[int, Player] = {
            core.auth.uid_of(p.client): p
            for p in players if isinstance(p, HumanPlayer)
        }

        items = {m[k]: v for k, v in core.item.items_of(g).items()}

        try:
            cls = g.bootstrap
            if core.game.should_halt(g):
                cls = HaltOnStart
            g.process_action(cls(params, items, players))
        except GameEnded as e:
            core.game.set_winners(g, list(e.winners))
        except Exception:
            core.game.mark_crashed(g)
            raise
        finally:
            g.ended = True
            core.events.game_ended.emit(g)

    def __repr__(g) -> str:
        core = g.core
        try:
            gid = str(core.room.gid_of(g))
        except Exception:
            gid = 'X'

        return '%s:%s' % (g.__class__.__name__, gid)

    def get_synctag(g) -> int:
        core = g.core
        # assert gevent.getcurrent() is core.room.greenlet_of(g)
        if core.game.is_aborted(g):
            raise GreenletExit

        g.synctag += 1
        return g.synctag

    def is_dropped(g, p: Player) -> bool:
        core = g.core
        if isinstance(p, HumanPlayer):
            return not core.room.is_online(g, p.client)
        elif isinstance(p, NPCPlayer):
            return False
        else:
            assert False, 'WTF!'

    def pause(self, time: float) -> None:
        gevent.sleep(time)


class HumanPlayer(Player):
    client: Client

    def __init__(self, g: Game, uid: int, client: Client):
        self.game = g
        self.uid = uid
        self.client = client

    def reveal(self, ol: Any) -> None:
        g = self.game
        core = g.core
        st = g.get_synctag()
        core.game.write(g, self.client, 'Sync:%d' % st, ol)  # XXX encode?


class NPCPlayer(Player):

    def __init__(self, g: Game, name: str, handler: Callable[[InputTransaction, Inputlet], Any]):
        self.game = g
        self.uid = 0
        self.name = name
        self.handle_user_input = handler

    def reveal(self, ol: Any) -> None:
        self.game.get_synctag()
