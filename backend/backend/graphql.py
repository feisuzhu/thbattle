# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import graphene as gh

# -- own --
from game.schema import GameOps, GameQuery
# from guild.schema import GuildOps, GuildQuery
from item.schema import ItemOps
from player.schema import PlayerOps, PlayerQuery, UserOps, UserQuery
from system.schema import SystemOps, SystemQuery
from unlock.schema import UnlockOps


# -- code --
class ResolveDebugMiddleware(object):
    def resolve(self, next, root, info, **args):
        p = next(root, info, **args)
        if p.is_rejected:
            try:
                __traceback_hide__ = True  # noqa: F841
                p.get()
            except Exception:
                from backend.debug import state
                rv = state.collect()
                import logging
                log = logging.getLogger('autopsy')
                log.error(f'!!! Exception Autopsy: http://localhost:8000/.debug/console/{rv["id"]}')
        return p


Query = type('Query', (
    UserQuery,
    PlayerQuery,
    GameQuery,
    SystemQuery,
    gh.ObjectType
), {})


Mutation = type('Mutation', (
    UserOps,
    PlayerOps,
    GameOps,
    ItemOps,
    UnlockOps,
    SystemOps,
    gh.ObjectType,
), {})

schema = gh.Schema(query=Query, mutation=Mutation)
