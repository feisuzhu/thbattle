# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from graphene_django.types import DjangoObjectType
import graphene as gh

# -- own --
from . import models


# -- code --
class Guild(DjangoObjectType):
    class Meta:
        model = models.Guild


# ---------------------------
class GuildQuery(gh.ObjectType):
    guild = gh.Field(
        Guild,
        id=gh.Int(description="势力ID"),
        name=gh.String(description='势力名称'),
        description='获取势力',
    )
    guilds = gh.List(
        gh.NonNull(Guild),
        keyword=gh.String(required=True, description='关键词'),
        description='查找势力',
    )

    @staticmethod
    def resolve_guild(root, info, id=None, name=None):
        if id is not None:
            return models.Guild.objects.get(id=id)
        elif name is not None:
            return models.Guild.objects.get(name=name)

    @staticmethod
    def resolve_guilds(root, info, keyword):
        return models.Guild.objects.filter(name__contains=keyword)


class GuildOps(gh.ObjectType):
    create = gh.Field(
        Guild,
        name=gh.String(required=True, description="势力名称"),
        slogan=gh.String(required=True, description="势力口号"),
        totem=gh.String(description="势力图腾（图片URL）"),
        description="创建势力",
    )

    transfer = gh.Boolean(
        guild_id=gh.Int(required=True, description="势力ID"),
        to=gh.Int(required=True, description="接收人用户ID"),
        description="转让势力",
    )

    join = gh.Boolean(
        guild_id=gh.Int(required=True, description="势力ID"),
        description="申请加入势力",
    )

    approve = gh.Boolean(
        player_id=gh.Int(required=True, description="玩家ID"),
        description="批准加入势力",
    )

    kick = gh.Boolean(
        player_id=gh.Int(required=True, description="玩家ID"),
        description="踢出势力",
    )

    quit = gh.Boolean(
        description="退出势力",
    )

    update = gh.Field(
        Guild,
        slogan=gh.String(description="口号"),
        totem=gh.String(description="图腾（URL）"),
        description="更新势力信息",
    )
