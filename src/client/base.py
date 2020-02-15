# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from copy import copy
from random import Random
from typing import Any, Optional, Sequence, TYPE_CHECKING, cast
import logging

# -- third party --
from gevent import Greenlet
import gevent

# -- own --
from game.base import Game, GameAbort, GameEnded, GameRunner, InputTransaction, Inputlet, Player
from game.base import TimeLimitExceeded

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('client.base')


class ForcedKill(gevent.GreenletExit):
    pass


class Theone(Player):

    def __init__(self, game: Game, uid: int):
        Player.__init__(self)
        self.game = game
        self.uid = uid

    def reveal(self, obj: Any) -> None:
        # It's me, server will tell me what the hell these is.
        g = self.game
        core = cast(ClientGameRunner, g.runner).core
        st = g.get_synctag()
        _, raw = core.game.gamedata_of(g).gexpect(f'Sync:{st}')
        if isinstance(obj, (list, tuple)):
            for o, rd in zip(obj, raw):
                o.sync(rd)
        else:
            obj.sync(raw)


class Someone(Player):

    def __init__(self, game: Game, uid: int):
        Player.__init__(self)
        self.game = game
        self.uid = uid

    def reveal(self, ol: Any) -> None:
        # Peer player, won't reveal.
        self.game.get_synctag()  # must sync


class ClientGameRunner(GameRunner):
    game: Game
    core: Core

    def __init__(self, core: Core, g: Game):
        self.core = core
        self.game = g
        super().__init__()

    def _run(self) -> None:
        g = self.game

        g.runner = self
        g.synctag = 0
        g.random = Random()
        core = self.core
        core.events.game_started.emit(g)
        params = core.game.params_of(g)
        items = core.game.items_of(g)
        players = core.game.players_of(g)

        try:
            g.process_action(g.bootstrap(params, items, players))
        except GameEnded as e:
            g.winners = e.winners
        except GameAbort:
            pass
        finally:
            g.ended = True

        core.events.client_game_finished.emit(g)

    def pause(self, time: float) -> None:
        gevent.sleep(time)

    def is_dropped(self, p: Player) -> bool:
        core = self.core
        return core.game.is_dropped(self.game, p)

    def is_aborted(self) -> bool:
        return False

    def get_side(self) -> str:
        return 'client'

    def user_input(
        self,
        entities: Sequence[Any],
        inputlet: Inputlet,
        timeout: int = 25,
        type: str = 'single',
        trans: Optional[InputTransaction] = None,
    ):

        assert type in ('single', 'all', 'any')
        assert not type == 'single' or len(entities) == 1

        timeout = max(0, timeout)

        inputlet.timeout = timeout
        entities = list(entities)

        if not trans:
            with InputTransaction(inputlet.tag(), entities) as trans:
                return self.user_input(entities, inputlet, timeout, type, trans)

        g = self.game
        assert isinstance(g, Game)
        core = self.core

        t = {'single': '', 'all': '&', 'any': '|'}[type]
        tag = 'I{0}:{1}:'.format(t, inputlet.tag())

        ilets = {e: copy(inputlet) for e in entities}
        for e in entities:
            ilets[e].actor = e

        inputproc: Optional[Greenlet] = None

        me = core.game.theone_of(g)

        results = {e: None for e in entities}

        synctags = {e: g.get_synctag() for e in entities}
        synctags_r = {v: k for k, v in synctags.items()}

        def get_player(e):
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

        def input_func(st: str) -> None:
            my = ilets[p2e[me]]
            with TimeLimitExceeded(timeout + 1, False):
                _, my = g.emit_event('user_input', (trans, my))

            core.game.write(g, f'{tag}{st}', my.data())

        try:
            for e in entities:
                g.emit_event('user_input_start', (trans, ilets[e]))

            if me in p2e:  # me involved
                if not core.game.is_observe(g):
                    inputproc = core.runner.spawn(input_func, synctags[p2e[me]])

            orig_entities = entities[:]
            inputany_entity = None

            g.emit_event('user_input_begin_wait_resp', trans)  # for replay speed control
            while entities:
                # should be [tag, <Data for Inputlet.parse>]
                # tag likes 'RI?:ChooseOption:2345'
                tag_, data = core.game.gamedata_of(g).gexpect('R%s*' % tag)
                st = int(tag_.split(':')[2])
                if st not in synctags_r:
                    log.warning('Unexpected sync tag: %d', st)
                    continue

                e = synctags_r[st]

                my = ilets[e]

                try:
                    rst = my.parse(data)
                except Exception:
                    log.exception('user_input: exception in .process()')
                    # ----- FOR DEBUG -----
                    if g.IS_DEBUG:
                        raise
                    # ----- END FOR DEBUG -----
                    rst = None

                rst = my.post_process(e, rst)

                g.emit_event('user_input_finish', (trans, my, rst))

                entities.remove(e)
                results[e] = rst

                # also remove from synctags
                del synctags_r[st]
                del synctags[e]

                if type == 'any' and rst is not None:
                    assert not inputany_entity
                    inputany_entity = e

            g.emit_event('user_input_end_wait_resp', trans)  # for replay speed control

        finally:
            inputproc and [inputproc.kill(), inputproc.join()]

        if type == 'single':
            return results[orig_entities[0]]

        elif type == 'any':
            if not inputany_entity:
                return None, None

            return inputany_entity, results[inputany_entity]

        elif type == 'all':
            # return OrderedDict([(i, results[i]) for i in orig_entities])
            return {e: results[e] for e in orig_entities}

        assert False, 'WTF?!'
