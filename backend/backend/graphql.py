# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import graphene as gh
import graphql

# -- own --
from game.schema import GameOps, GameQuery
# from guild.schema import GuildOps, GuildQuery
from item.schema import ItemOps
from player.schema import PlayerOps, PlayerQuery
from system.schema import SystemOps, SystemQuery
from unlock.schema import UnlockOps
from authext.schema import UserQuery, UserOps
from ranking.schema import RankingOps
from chat.schema import ChatQuery, ChatOps


# -- code --
# class ResolveDebugMiddleware(object):
#     def resolve(self, next, root, info, **args):
#         p = next(root, info, **args)
#         if p.is_rejected:
#             try:
#                 __traceback_hide__ = True  # noqa: F841
#                 p.get()
#             except Exception:
#                 from backend.debug import state
#                 rv = state.collect()
#                 import logging
#                 log = logging.getLogger('autopsy')
#                 log.error(f'!!! Exception Autopsy: http://localhost:8000/.debug/console/{rv["id"]}')
#         return p


class ResolveDebugMiddleware(object):
    def resolve(self, next, root, info, **args):
        p = next(root, info, **args)
        # FIXME: not working, disabling for now
        return p

        if not p.is_rejected:
            return p

        if isinstance(p.reason, graphql.error.GraphQLError):
            return p

        from backend.debug import state
        rv = state.collect_exception(p.reason)
        import logging
        log = logging.getLogger('autopsy')
        log.error(r'+-------------------------------+')
        log.error(f'| !! Resolver Exception Autopsy | http://localhost:8000/.debug/console/{rv["id"]}')
        log.error(r'+-------------------------------+')
        return p


Query = type('Query', (
    UserQuery,
    PlayerQuery,
    GameQuery,
    SystemQuery,
    ChatQuery,
    gh.ObjectType
), {})


Mutation = type('Mutation', (
    UserOps,
    PlayerOps,
    GameOps,
    ItemOps,
    UnlockOps,
    SystemOps,
    RankingOps,
    ChatOps,
    gh.ObjectType,
), {})

schema = gh.Schema(query=Query, mutation=Mutation)
