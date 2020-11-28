# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from copy import copy
from typing import Any, Callable, Dict, Optional, Sequence, TYPE_CHECKING, Tuple, cast
import logging

# -- third party --
from gevent import Greenlet, iwait
from gevent.pool import Group as GreenletGroup

# -- own --
from endpoint import EndpointDied
from game.base import Game, GameAbort, GameEnded, GameRunner, InputTransaction, Inputlet, Player
from game.base import TimeLimitExceeded
from server.endpoint import Client

# -- typing --
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
            tag, rst = core.game.gamedata_of(g, p.client).gexpect([t])
            return rst
        except EndpointDied:
            return None

    def __repr__(self) -> str:
        return f'InputWaiter:[{self.tag}]'


class InputWaiterGroup(GreenletGroup):
    greenlet_class = InputWaiter


class ServerGameRunner(GameRunner):

    game: Game
    core: Core

    def __init__(self, core: Core, g: Game):
        self.core = core
        self.game = g
        super().__init__()

    def _run(self) -> None:
        core = self.core
        g = self.game

        gid = core.room.gid_of(g)
        self.gr_name = f'{repr(g)}:{gid}'

        g.runner = self
        g.synctag = 0

        core.events.game_started.emit(g)

        params = core.game.params_of(g)
        players = core.game.players_of(g)

        m: Dict[int, Player] = {
            core.auth.pid_of(p.client): p
            for p in players if isinstance(p, HumanPlayer)
        }

        items = {m[k]: v for k, v in core.item.items_of(g).items()}

        try:
            cls = g.bootstrap
            g.process_action(cls(params, items, players))
        except GameEnded as e:
            core.game.set_winners(g, list(e.winners))
        except GameAbort:
            # caused by last player leave,
            # events will be handled by lobby
            return

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
            assert False, f'WTF: {p} is not a Player'

    def pause(self, time: float) -> None:
        core = self.core
        if not core.options.testing:
            core.runner.sleep(time)

    def is_aborted(self) -> bool:
        core = self.core
        return core.game.is_aborted(self.game)

    def user_input(
        self,
        entities: Sequence[Any],
        inputlet: Inputlet,
        timeout: int = 25,
        type: str = 'single',
        trans: Optional[InputTransaction] = None,
    ) -> Any:
        if not trans:
            with InputTransaction(inputlet.tag(), entities) as trans:
                return self.user_input(entities, inputlet, timeout, type, trans)

        core = self.core

        assert entities
        assert type in ('single', 'all', 'any')
        assert not type == 'single' or len(entities) == 1

        timeout = max(0, timeout)

        inputlet.timeout = timeout
        g = cast(Game, trans.game)

        entities = list(entities)

        t = {'single': '', 'all': '&', 'any': '|'}[type]
        tag = 'I{0}:{1}:'.format(t, inputlet.tag())

        ilets = {e: copy(inputlet) for e in entities}
        for e in entities:
            ilets[e].actor = e

        results = {e: None for e in entities}
        synctags = {e: g.get_synctag() for e in entities}

        orig_entities = entities[:]
        waiters = InputWaiterGroup()

        def get_player(e: Any) -> Player:
            if isinstance(e, Player):
                return e
            elif hasattr(e, 'get_player'):
                p = e.get_player()
                assert isinstance(p, Player), f'{e}.get_player() == {p}, not a Player'
                return p
            else:
                raise Exception(f'Do not know how to process {e}')

        e2p = {e: get_player(e) for e in entities}
        p2e = {p: e for e, p in e2p.items()}

        try:
            inputany_entity = None

            for e in entities:
                p = e2p[e]
                if isinstance(p, NPCPlayer):
                    ilet = ilets[e]
                    p.handle_user_input(trans, ilet)
                    w = Greenlet(lambda _: ilet.data(), None)
                    w.player = p
                    waiters.start(w)
                else:
                    t = tag + str(synctags[e])
                    waiters.spawn(self, p, t)

            for e in entities:
                g.emit_event('user_input_start', (trans, ilets[e]))

            bottom_halves: Any = []  # FIXME: proper typing

            def flush() -> None:
                for t, data, trans, my, rst in bottom_halves:
                    for u in core.room.users_of(g):
                        core.game.write(g, u, t, data)

                    g.emit_event('user_input_finish', (trans, my, rst))

                bottom_halves[:] = []

            for w in iwait(waiters, timeout=timeout + 5):
                try:
                    rst = w.get()
                    p, data = w.player, rst
                except Exception:
                    if core.options.testing:
                        raise
                    log.exception('Error waiting user input, returning default')
                    p, data = w.player, None

                e = p2e[p]
                my = ilets[e]

                try:
                    rst = my.parse(data)
                except Exception:
                    if core.options.testing:
                        raise
                    log.exception('user_input: exception in .process()')
                    rst = None

                rst = my.post_process(e, rst)

                bottom_halves.append((
                    'R{}{}'.format(tag, synctags[e]), data, trans, my, rst
                ))

                entities.remove(e)
                results[e] = rst

                if type != 'any':
                    flush()

                if type == 'any' and rst is not None:
                    inputany_entity = e
                    break

        except TimeLimitExceeded:
            pass

        finally:
            waiters.kill()

        # flush bottom halves
        flush()

        # timed-out entities
        for e in entities:
            my = ilets[e]
            rst = my.parse(None)
            rst = my.post_process(e, rst)
            results[e] = rst
            g.emit_event('user_input_finish', (trans, my, rst))
            core = self.core
            t = 'R{}{}'.format(tag, synctags[e])
            for u in core.room.users_of(g):
                core.game.write(g, u, t, None)

        if type == 'single':
            return results[orig_entities[0]]

        elif type == 'any':
            if not inputany_entity:
                return None, None

            return inputany_entity, results[inputany_entity]

        elif type == 'all':
            # return OrderedDict([(p, results[p]) for p in orig_entities])
            return {e: results[e] for e in orig_entities}

        assert False, 'WTF?!'


class HumanPlayer(Player):
    client: Client

    def __init__(self, g: Game, pid: int, client: Client):
        self.game = g
        self.pid = pid
        self.client = client

    def reveal(self, obj: Any) -> None:
        g = self.game
        core = cast(ServerGameRunner, g.runner).core
        st = g.get_synctag()

        if isinstance(obj, (list, tuple)):
            encoded = [o.dump() for o in obj]
        else:
            encoded = obj.dump()

        core.game.write(g, self.client, f'Sync:{st}', encoded)


class NPCPlayer(Player):

    def __init__(self, g: Game, pid: int, handler: Callable[[InputTransaction, Inputlet], Any]):
        self.game = g
        self.pid = pid
        self.handle_user_input = handler

    def reveal(self, ol: Any) -> None:
        self.game.get_synctag()
