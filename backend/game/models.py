# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.db import models
from django.contrib.postgres import fields as pg

# -- own --
from player.models import Player


_ = lambda s: {'help_text': s, 'verbose_name': s}


# -- code --
class Game(models.Model):

    class Meta:
        verbose_name        = '完结的游戏'
        verbose_name_plural = '完结的游戏'

    id         = models.IntegerField(**_('游戏ID'), primary_key=True)
    name       = models.CharField(**_('游戏名称'), max_length=100)
    type       = models.CharField(**_('游戏类型'), max_length=20)
    flags      = pg.JSONField(**_('游戏选项'))
    players    = models.ManyToManyField(Player, **_('参与玩家'), related_name='+')
    winners    = models.ManyToManyField(Player, **_('胜利玩家'), related_name='+')
    started_at = models.DateTimeField(auto_now_add=True, **_('开始时间'))
    duration   = models.PositiveIntegerField(**_('持续时间'))

    def __str__(self):
        return f'[{self.gid}]self.name'


class GameReward(models.Model):

    class Meta:
        verbose_name        = '游戏积分'
        verbose_name_plural = '游戏积分'

    id     = models.AutoField(primary_key=True)
    game   = models.ForeignKey(Game, **_('游戏'), related_name='rewards', on_delete=models.CASCADE)
    player = models.ForeignKey(Player,  **_('玩家'), on_delete=models.CASCADE)
    type   = models.CharField(**_('积分类型'), max_length=20)
    amount = models.PositiveIntegerField(**_('数量'))

    def __str__(self):
        return f'{self.player.name}[{self.type}:{self.amount}]'


class GameArchive(models.Model):

    class Meta:
        verbose_name        = '游戏 Replay 存档'
        verbose_name_plural = '游戏 Replay 存档'

    game = models.OneToOneField(Game,
        **_('游戏'),
        primary_key=True,
        related_name='archive',
        on_delete=models.CASCADE,
    )
    replay = models.BinaryField(**_('Replay 数据'))

    def __str__(self):
        return self.game.name
