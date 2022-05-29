# -*- coding: utf-8 -*-

# -- stdlib --
import base64

# -- third party --
from django.core.cache import caches
from django.db import transaction
from graphene.types import generic as ghg
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
import graphene as gh
import trueskill

# -- own --
from . import models
from utils.graphql import Paging, require_perm


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


TS = trueskill.TrueSkill(draw_probability=0.0)


class RankingAdjustment(gh.ObjectType):
    player       = gh.Field('player.schema.Player', required=True, description='玩家')
    score_before = gh.Int(required=True, description='调整前积分')
    score_after  = gh.Int(required=True, description='调整后积分')
    changes      = gh.Int(required=True, description='变动次数(10以下视为未定级)')


class GameOps(gh.ObjectType):
    GmArchive = gh.Field(
        Game,
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

            g = models.Game(
                id=game.game_id,
                name=game.name,
                type=game.type,
                flags=game.flags,
                players=players,
                winners=[p for p in players if p.id in game.winners],
                started_at=game.started_at,
                duration=game.duration,
            )
            ar = models.GameArchive(game=g, replay=base64.b64decode(archive))
            g.save()
            ar.save()

        return g

    GmAddReward = gh.Field(
        Game,
        game_id=gh.Int(required=True, description='游戏ID'),
        rewards=gh.List(gh.NonNull(GameRewardInput), required=True, description='积分列表'),
        description='增加游戏积分',
    )

    @staticmethod
    def resolve_GmAddReward(root, info, game_id, rewards):
        ctx = info.context
        require_perm(ctx, 'game.add_gamereward')
        with transaction.atomic():
            g = models.Game.objects.get(id=game_id)
            for r in rewards:
                o = models.GameReward(
                    game=g,
                    player=models.Player.objects.get(id=r.player_id),
                    type=r.type,
                    amount=r.amount,
                )
                o.save()

                # TODO: add to Player profile
            return g

    GmAllocGameId = gh.Int(required=True, description="分配游戏ID")

    @staticmethod
    def resolve_GmAllocGameId(root, info):
        c = caches['default']
        c.get_or_set('next_game_id', lambda: 0)
        return c.incr('next_game_id')
