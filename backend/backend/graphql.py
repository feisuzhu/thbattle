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
