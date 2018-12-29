# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from graphene.types import generic as ghg
from graphene_django.types import DjangoObjectType
import graphene as gh

# -- own --
from . import models
from player.schema import Player
from utils.graphql import Paging


# -- code --
class Game(DjangoObjectType):
    class Meta:
        model = models.Game

    flags = ghg.GenericScalar(description='游戏选项', required=True)


class GameReward(DjangoObjectType):
    class Meta:
        model = models.GameReward


class GameArchive(DjangoObjectType):
    class Meta:
        model = models.GameArchive
        exclude_fields = ['replay']

    exists = gh.Boolean(description='Replay 数据存在？')
    replay = gh.String(description='Replay 数据（Base64）')


# ---------------------------
class GameQuery(gh.ObjectType):
    games = gh.List(
        Game,
        keyword=gh.String(description="关键字"),
        paging=Paging(description="分页"),
        description='获取游戏列表',
    )

    game = gh.Field(
        Game,
        id=gh.Int(required=True, description="游戏ID"),
        description='获取游戏',
    )

    '''
    @staticmethod
    def resolve_guild(root, info, id=None, name=None):
        if id is not None:
            return models.Game.objects.get(id=id)
        elif name is not None:
            return models.Game.objects.get(name=name)
'''


class GameInput(gh.InputObjectType):
    game_id    = gh.Int(required=True, description='游戏ID')
    name       = gh.String(required=True, description='游戏名称')
    type       = gh.String(required=True, description='游戏类型')
    flags      = ghg.GenericScalar(required=True, description='游戏选项')
    players    = gh.List(gh.NonNull(gh.Int), required=True, description='参与玩家UID')
    winners    = gh.List(gh.NonNull(gh.Int), required=True, description='胜利玩家UID')
    started_at = gh.DateTime(auto_now_add=True, required=True, description='开始时间')
    duration   = gh.Int(required=True, description='持续时间')


class GameRewardInput(gh.InputObjectType):
    player_id  = gh.Int(required=True, description='玩家ID')
    type       = gh.String(required=True, description='积分类型')
    amount     = gh.Int(required=True, description='数量')


class GameOps(gh.ObjectType):
    archive = gh.Field(
        Game,
        game=gh.Argument(GameInput, required=True, description='游戏元数据'),
        archive=gh.String(required=True, description='游戏 Replay 数据（Base64）'),
        description='保存游戏存档',
    )
    add_reward = gh.Field(
        Game,
        game_id=gh.Int(required=True, description='游戏ID'),
        rewards=gh.List(gh.NonNull(GameRewardInput), required=True, description='积分列表'),
        description='增加游戏积分',
    )
