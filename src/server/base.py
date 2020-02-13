# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from copy import copy
from typing import Any, Callable, Dict, List, Optional, Sequence, TYPE_CHECKING, Tuple, cast
import logging

# -- third party --
from gevent import Greenlet, iwait
from gevent.pool import Group as GreenletGroup
import gevent

# -- own --
from endpoint import EndpointDied
from game.base import BootstrapAction, Game, GameEnded, GameItem, GameRunner, InputTransaction, GameAbort
from game.base import Inputlet, Player, TimeLimitExceeded
from server.endpoint import Client
from utils.misc import BatchList


# -- code --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Game_Server')


class InputWaiter(Greenlet):
    def __init__(self, runner: ServerGameRunner, player: HumanPlayer, tag: str):
        Greenlet.__init__(self)
        self.runner = runner
        self.player = player
        self.tag = tag

    def _run(self) -> Optional[Tuple[str, Any]]:
        p, t = self.player, self.tag
        core = self.runner.core
        g = self.runner.game
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
        core = cast(ServerGameRunner, g.runner).core
        core.game.set_bootstrap_action(g, self)
        g.pause(99999999)
        return True


class ServerGameRunner(GameRunner):

    game: Game
    core: Core

    def __init__(self, core: Core):
        self.core = core
        super().__init__()

    def run(self, g: Game) -> None:
        self.game = g
        g.synctag = 0
        core = self.core

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
        except GameAbort:
            # caused by last player leave,
            # events will be handled by lobby
            return
        except Exception:
            core.game.mark_crashed(g)
            raise
        finally:
            g.ended = True
            core.events.game_ended.emit(g)

    # def __repr__(g) -> str:
    #     core = g.core
    #     try:
    #         gid = str(core.room.gid_of(g))
    #     except Exception:
    #         gid = 'X'

    #     return '%s:%s' % (g.__class__.__name__, gid)

    def get_side(self) -> str:
        return 'server'

    def is_dropped(self, p: Player) -> bool:
        core = self.core
        g = self.game
        if isinstance(p, HumanPlayer):
            return not core.room.is_online(g, p.client)
        elif isinstance(p, NPCPlayer):
            return False
        else:
            assert False, 'WTF!'

    def pause(self, time: float) -> None:
        gevent.sleep(time)

    def is_aborted(self) -> bool:
        core = self.core
        return core.game.is_aborted(self.game)

    def user_input(
        self,
        players: Sequence[Any],
        inputlet: Inputlet,
        timeout: int = 25,
        type: str = 'single',
        trans: Optional[InputTransaction] = None,
    ) -> Any:
        if not trans:
            with InputTransaction(inputlet.tag(), players) as trans:
                return self.user_input(players, inputlet, timeout, type, trans)

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
                    waiters.start(Greenlet(lambda v: v, ilet.data()))
                else:
                    t = tag + str(synctags[p])
                    waiters.spawn(self, p, t)

            for p in players:
                g.emit_event('user_input_start', (trans, ilets[p]))

            bottom_halves: Any = []  # FIXME: proper typing

            def flush() -> None:
                core = self.core
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
            core = self.core
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
            # return OrderedDict([(p, results[p]) for p in orig_players])
            return {p: results[p] for p in orig_players}

        assert False, 'WTF?!'


class HumanPlayer(Player):
    client: Client

    def __init__(self, g: Game, uid: int, client: Client):
        self.game = g
        self.uid = uid
        self.client = client

    def reveal(self, ol: Any) -> None:
        g = self.game
        core = cast(ServerGameRunner, g.runner).core
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
