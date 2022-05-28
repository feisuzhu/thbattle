# -*- coding: utf-8 -*-

# -- stdlib --
import itertools
# -- third party --
from django.core.cache import caches
from django.db import transaction, IntegrityError
from graphene.types import generic as ghg
from graphene_django.types import DjangoObjectType
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
    GmAddReward = gh.Field(
        Game,
        game_id=gh.Int(required=True, description='游戏ID'),
        rewards=gh.List(gh.NonNull(GameRewardInput), required=True, description='积分列表'),
        description='增加游戏积分',
    )

    GmAllocGameId = gh.Int(required=True, description="分配游戏ID")

    @staticmethod
    def resolve_GmAllocGameId(root, info):
        c = caches['default']
        c.get_or_set('next_game_id', lambda: 0)
        return c.incr('next_game_id')

    GmAddReward = gh.Field(
        Game,
        game_id=gh.Int(required=True, description='游戏ID'),
        rewards=gh.List(gh.NonNull(GameRewardInput), required=True, description='积分列表'),
        description='增加游戏积分',
    )

    GmAdjustRanking = gh.Field(
        gh.List(gh.NonNull(RankingAdjustment), required=True),
        required=True,
        category=gh.String(required=True, description='分类'),
        winners=gh.List(gh.Int, required=True, description='赢家 PID 列表'),
        losers=gh.List(gh.Int, required=True, description='败者 PID 列表'),
    )

    @staticmethod
    def resolve_GmAdjustRanking(root, info, category, winners, losers):
        ctx = info.context

        require_perm(ctx, 'game.change_ranking')
        players = {v.id: v for v in models.Player.objects.filter(id__in=winners+losers)}
        if set(players) != set(winners+losers):
            raise Exception('有不存在的玩家')

        def get_ranking(p):
            try:
                return models.Ranking.objects.get(player=p, category=category, season=season)
            except models.Ranking.DoesNotExist:
                return models.Ranking(player=p, category=category, season=season)

        for _ in range(3):
            try:
                with transaction.atomic():
                    import system
                    season = int(system.models.Setting.objects.get(key='ranking-season').value)
                    wl = [get_ranking(players[i]) for i in winners]
                    ll = [get_ranking(players[i]) for i in losers]
                    wrl = [TS.create_rating(mu=v.mu, sigma=v.sigma) for v in wl]
                    lrl = [TS.create_rating(mu=v.mu, sigma=v.sigma) for v in ll]
                    nwrl, nlrl = TS.rate([wrl, lrl], [0, 1])

                    rst = []
                    for obj, b4, af in itertools.chain(zip(wl, wrl, nwrl), zip(ll, lrl, nlrl)):
                        obj.mu = af.mu
                        obj.sigma = af.sigma
                        obj.changes += 1
                        obj.save()
                        rst.append(RankingAdjustment(
                            player=players[obj.player.id],
                            score_before=models.Ranking.score_from_tsranking(b4),
                            score_after=models.Ranking.score_from_tsranking(af),
                            changes=obj.changes,
                        ))

                    return rst

            except IntegrityError as e:
                exc = e
                continue

        raise exc
