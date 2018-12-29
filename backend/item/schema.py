# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from graphene_django.types import DjangoObjectType
import graphene as gh

# -- own --
from . import models


# -- code --
class Item(DjangoObjectType):
    class Meta:
        model = models.Item


'''
class ItemActivity(DjangoObjectType):
    class Meta:
        model = models.ItemActivity
'''


class ExchangeItem(DjangoObjectType):
    class Meta:
        model = models.Exchange


class ExchangeQuery(gh.ObjectType):
    exchange = gh.List(gh.NonNull(ExchangeItem), description="交易所")

    @staticmethod
    def resolve_exchange(root, info):
        return models.Exchange.objects.order_by('-id')


class ExchangeOps(gh.ObjectType):
    buy    = gh.Field(Item, exchangeId=gh.Int(required=True, description="交易条目ID"), description="购买")
    sell   = gh.Field(ExchangeItem, itemId=gh.Int(required=True, description="物品ID"), description="出售")
    cancel = gh.Boolean(exchangeId=gh.Int(required=True, description="交易条目ID"), description="取消出售")


class ItemOps(gh.ObjectType):
    add = gh.Field(
        Item,
        player=gh.Int(required=True, description="玩家ID"),
        typ=gh.String(required=True, description="物品类型"),
        reason=gh.String(required=True, description="原因"),
        description="给予玩家一个物品",
    )
    remove = gh.Boolean(
        player=gh.Int(required=True, description="玩家ID"),
        typ=gh.String(required=True, description="物品类型"),
        reason=gh.String(required=True, description="原因"),
        description="移除玩家的一个物品",
    )
