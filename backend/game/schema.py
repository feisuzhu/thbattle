# -*- coding: utf-8 -*-

# -- stdlib --
import base64

# -- third party --
from django.db import transaction
from graphene.types import generic as ghg
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
import graphene as gh

# -- own --
from . import models
from backend.cache import rdb
from utils.graphql import Paging, require_perm


# -- code --
class Game(DjangoObjectType):
    class Meta:
        model = models.Game
        fields = '__all__'

    flags = ghg.GenericScalar(description='游戏选项', required=True)


class GameReward(DjangoObjectType):
    class Meta:
        model = models.GameReward
        fields = '__all__'


class GameArchive(DjangoObjectType):
    class Meta:
        model = models.GameArchive
        fields = ['game']

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

    @staticmethod
    def resolve_game(root, info, id):
        return models.Game.objects.filter(id=id).first()


class GameInput(gh.InputObjectType):
    game_id    = gh.Int(required=True, description='游戏ID')
    name       = gh.String(required=True, description='游戏名称')
    type       = gh.String(required=True, description='游戏类型')
    flags      = ghg.GenericScalar(required=True, description='游戏选项')
    players    = gh.List(gh.NonNull(gh.Int), required=True, description='参与玩家UID')
    winners    = gh.List(gh.NonNull(gh.Int), required=True, description='胜利玩家UID')
    deserters  = gh.List(gh.NonNull(gh.Int), required=True, description='逃跑玩家UID')
    started_at = gh.DateTime(auto_now_add=True, required=True, description='开始时间')
    duration   = gh.Int(required=True, description='持续时间')


class GameOps(gh.ObjectType):
    GmArchive = gh.Field(
        gh.NonNull(Game),
        game=gh.Argument(GameInput, required=True, description='游戏元数据'),
        archive=gh.String(required=True, description='游戏 Replay 数据（Base64）'),
        description='保存游戏存档',
    )

    @staticmethod
    def resolve_GmArchive(root, info, game, archive):
        ctx = info.context
        require_perm(ctx, 'game.add_game')
        require_perm(ctx, 'game.add_gamearchive')

        with transaction.atomic():
            if not set(game.winners) <= set(game.players):
                raise GraphQLError('赢家不在玩家列表内')

            players = models.Player.objects.filter(id__in=game.players)
            if len(players) != len(game.players):
                raise GraphQLError('有不存在的玩家')

            if models.Game.objects.filter(id=game.game_id).exists():
                raise GraphQLError('游戏重复')

            if models.GameArchive.objects.filter(game_id=game.game_id).exists():
                raise GraphQLError('游戏 Archive 重复')

            g = models.Game(
                id=game.game_id,
                name=game.name,
                type=game.type,
                flags=game.flags,
                started_at=game.started_at,
                duration=game.duration,
            )
            g.save()
            g.players.set(players)
            g.winners.set([p for p in players if p.id in game.winners])
            g.deserters.set([p for p in players if p.id in game.deserters])
            ar = models.GameArchive(game=g, replay=base64.b64decode(archive))
            g.save()
            ar.save()

        return g

    GmSettleRewards = gh.List(
        gh.NonNull(GameReward),
        required=True,
        game=gh.Argument(GameInput, required=True, description='游戏元数据'),
        description='结算游戏奖励',
    )

    @staticmethod
    def resolve_GmSettleRewards(root, info, game):
        ctx = info.context
        require_perm(ctx, 'game.add_gamereward')
        with transaction.atomic():
            # TODO: impl the stragegy
            g = models.Game.objects.get(id=game.game_id)
            rst = []
            for r in game.players:
                o = models.GameReward(
                    game=g,
                    player=models.Player.objects.get(id=r),
                    type="jiecao",
                    amount=1,
                )
                o.save()
                rst.append(o)

            # TODO: add to Player profile
            return rst

    GmAllocGameId = gh.Int(required=True, description="分配游戏ID")

    @staticmethod
    def resolve_GmAllocGameId(root, info):
        return rdb.incr('next_game_id')
