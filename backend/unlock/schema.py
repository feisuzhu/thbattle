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
class Achievement(DjangoObjectType):
    class Meta:
        model = models.Achievement


class Unlocked(DjangoObjectType):
    class Meta:
        model = models.Unlocked


class UnlockOps(gh.ObjectType):
    add_unlock = gh.Boolean(
        id=gh.Int(required=True, description="玩家ID"),
        item=gh.String(required=True, description="解锁项目代码"),
        description="解锁项目",
    )

    @staticmethod
    def resolve_add_unlock(root, info, id, item):
        ctx = info.context
        require_perm(ctx, 'unlock.add_unlock')
        p = Player.objects.get(id=id)
        if not p:
            raise GraphQLError('没有找到玩家')

        if not p.unlocks.filter(item=item).exists():
            p.unlocks.create(item=item)

        return True

    add_achievement = gh.Boolean(
        id=gh.Int(required=True, description="用户ID"),
        achievement=gh.String(required=True, description="成就代码"),
        description="增加成就",
    )

    @staticmethod
    def resolve_add_achievement(root, info, id, achievement):
        ctx = info.context
        require_perm(ctx, 'unlock.add_unlock')
        p = Player.objects.get(id=id)
        if not p:
            raise GraphQLError('没有找到玩家')

        if not p.achievements.filter(achievement=achievement).exists():
            p.achievements.create(achievement=achievement)

        return True
