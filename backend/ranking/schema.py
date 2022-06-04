# -*- coding: utf-8 -*-

# -- stdlib --
import itertools

# -- third party --
from django.db import IntegrityError, transaction
from graphene_django.types import DjangoObjectType
import graphene as gh
import trueskill

# -- own --
from . import models
from utils.graphql import require_perm
from game.schema import GameInput


# -- code --
TS = trueskill.TrueSkill(draw_probability=0.0)


class RankingHistory(DjangoObjectType):
    class Meta:
        model = models.RankingHistory


class RankingQuery(gh.ObjectType):
    pass


class RankingOps(gh.ObjectType):
    RkAdjustRanking = gh.Field(
        gh.List(gh.NonNull(RankingHistory), required=True),
        required=True,
        game=gh.Argument(GameInput, required=True, description='游戏元数据'),
    )

    @staticmethod
    def resolve_RkAdjustRanking(root, info, game):
        ctx = info.context

        pids = game.players
        winners = game.winners
        losers = [i for i in pids if i not in winners]
        category = game.type

        require_perm(ctx, 'game.change_ranking')
        players = {v.id: v for v in models.Player.objects.filter(id__in=pids)}
        if set(players) != set(pids):
            raise Exception('有不存在的玩家')

        def get_ranking(p):
            r = models.Ranking.objects.get_or_create(player=p, category=category, season=season)
            return r or models.Ranking(player=p, category=category, season=season)

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
                    for r, b4, af in itertools.chain(zip(wl, wrl, nwrl), zip(ll, lrl, nlrl)):
                        r.mu = af.mu
                        r.sigma = af.sigma
                        r.changes += 1
                        r.save()
                        h = models.RankingHistory(
                            game_id=game.game_id,
                            player=players[r.player.id],
                            season=season,
                            category=category,
                            score_before=models.Ranking.score_from_tsranking(b4),
                            score_after=models.Ranking.score_from_tsranking(af),
                            changes=r.changes,
                        )
                        h.save()
                        rst.append(h)

                    return rst

            except IntegrityError as e:
                exc = e
                continue

        raise exc
