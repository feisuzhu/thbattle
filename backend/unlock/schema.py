# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
import graphene as gh

# -- own --
from . import models
from player.models import Player
from utils.graphql import require_perm


# -- code --
class Unlocked(DjangoObjectType):
    class Meta:
        model = models.Unlocked


class UnlockOps(gh.ObjectType):
    UlAddUnlock = gh.Boolean(
        id=gh.Int(required=True, description="玩家ID"),
        item=gh.String(required=True, description="解锁项目代码"),
        description="解锁项目",
    )

    @staticmethod
    def resolve_UlAddUnlock(root, info, id, item):
        ctx = info.context
        require_perm(ctx, 'unlock.add_unlock')
        p = Player.objects.get(id=id)
        if not p:
            raise GraphQLError('没有找到玩家')

        if not p.unlocks.filter(item=item).exists():
            p.unlocks.create(item=item)

        return True
