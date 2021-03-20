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


class ItemOps(gh.ObjectType):
    ItAdd = gh.Field(
        Item,
        player=gh.Int(required=True, description="玩家ID"),
        sku=gh.String(required=True, description="物品SKU"),
        reason=gh.String(required=True, description="原因"),
        description="给予玩家一个物品",
    )
    ItRemove = gh.Boolean(
        player=gh.Int(required=True, description="玩家ID"),
        sku=gh.String(required=True, description="物品SKU"),
        reason=gh.String(required=True, description="原因"),
        description="移除玩家的一个物品",
    )
