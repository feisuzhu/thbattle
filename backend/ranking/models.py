# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.db import models

# -- own --
from player.models import Player
from game.models import Game

# -- code --
_ = lambda s: {'help_text': s, 'verbose_name': s}


class Ranking(models.Model):

    class Meta:
        verbose_name        = '天梯分数'
        verbose_name_plural = '天梯分数'

        constraints = [
            models.UniqueConstraint(fields=['player', 'season', 'category'], name='ranking_uniq')
        ]

    id       = models.IntegerField(**_('ID'), primary_key=True)
    player   = models.ForeignKey(Player, **_('玩家'), on_delete=models.CASCADE)
    season   = models.IntegerField(**_('赛季'))
    category = models.CharField(**_('分类'), max_length=20)
    changes  = models.IntegerField(**_('变动'), default=0)
    mu       = models.FloatField(**_('Mu'), default=25.0)
    sigma    = models.FloatField(**_('Sigma'), default=25.0/3)

    def __str__(self):
        return f'[#{self.id}][{self.player.id}:{self.category}](n={self.changes},μ={self.mu},σ={self.sigma})'

    @staticmethod
    def score_from_tsranking(r):
        return int((r.mu - r.sigma) * 100)

    def score(self):
        return int((self.mu - self.sigma) * 100)


class RankingHistory(models.Model):

    class Meta:
        verbose_name        = '天梯分数历史'
        verbose_name_plural = '天梯分数历史'

    id       = models.IntegerField(**_('ID'), primary_key=True)
    game     = models.ForeignKey(Game, **_('游戏'), on_delete=models.CASCADE, db_constraint=False, related_name='+')
    player   = models.ForeignKey(Player, **_('玩家'), on_delete=models.CASCADE, related_name='+')
    season   = models.IntegerField(**_('赛季'))
    category = models.CharField(**_('分类'), max_length=20)
    score    = models.IntegerField(**_('分数'))

    def __str__(self):
        return f'[#{self.id}][{self.game.id}:{self.player.name}:{self.category}] - {self.score}'
