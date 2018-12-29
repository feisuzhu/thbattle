# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
import graphene as gh

# -- own --
from guild.schema import GuildOps, GuildQuery
from item.schema import ExchangeOps, ExchangeQuery, ItemOps
from player.schema import PlayerOps, PlayerQuery
from game.schema import GameOps, GameQuery
from system.schema import SystemOps, SystemQuery
from unlock.schema import UnlockOps
from utils.graphql import stub
import badge.schema  # noqa


# -- code --
class Query(PlayerQuery, GameQuery, GuildQuery, ExchangeQuery, SystemQuery, gh.ObjectType):
    pass


class Mutation(gh.ObjectType):
    player   = stub(PlayerOps,   "用户/玩家")
    game     = stub(GameOps,     "游戏")
    guild    = stub(GuildOps,    "势力")
    item     = stub(ItemOps,     "物品")
    exchange = stub(ExchangeOps, "交易所")
    unlock   = stub(UnlockOps,   "解锁/成就")
    system   = stub(SystemOps,   "系统")


schema = gh.Schema(query=Query, mutation=Mutation)
