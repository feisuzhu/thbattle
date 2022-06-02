# -*- coding: utf-8 -*-

# -- stdlib --
import logging
import re

# -- third party --
from django.db import models
from django.utils import timezone

# -- own --
import authext.models


# -- code --
log = logging.getLogger("player.model")


def is_phone_number(value):
    if not isinstance(value, str):
        return False

    return bool(re.match(r'^(?!17[01])\d{11}$', value))


def is_name(value):
    return bool(re.match(r'^[^\s%*"<>&]{3,15}$', value))


class Player(models.Model):

    class Meta:
        verbose_name        = '玩家'
        verbose_name_plural = '玩家'

        permissions = (
            ("change_credit", "修改积分"),
        )

    id     = models.AutoField(verbose_name='ID', help_text='ID', primary_key=True)
    user   = models.OneToOneField(authext.models.User, models.CASCADE, verbose_name='用户', help_text='关联用户', unique=True)
    name   = models.CharField('昵称', unique=True, max_length=15, validators=[is_name], help_text='昵称')
    bio    = models.CharField('签名', blank=True, max_length=150, help_text='签名')
    avatar = models.URLField('头像', blank=True, max_length=150, help_text='头像')
    prefs  = models.TextField('个人设置', blank=True, help_text='个人设置')

    point = models.IntegerField('点', default=0, help_text='点')
    power = models.IntegerField('P', default=0, help_text='P')
    bomb = models.IntegerField('B', default=0, help_text='B')
    full = models.IntegerField('F', default=0, help_text='F')
    up = models.IntegerField('+1UP', default=0, help_text='+1UP')

    games  = models.IntegerField('游戏数', default=0, help_text='游戏数')
    drops  = models.IntegerField('逃跑数', default=0, help_text='逃跑数')

    # guild = models.ForeignKey(
    #     'guild.Guild', models.SET_NULL,
    #     related_name='members', verbose_name='势力',
    #     blank=True, null=True,
    #     help_text='势力',
    # )
    badges = models.ManyToManyField(
        'badge.Badge',
        related_name='players', verbose_name='勋章',
        blank=True,
        help_text='勋章',
    )
    friends = models.ManyToManyField(
        'self',
        related_name='friended_by', verbose_name='好友',
        symmetrical=False, blank=True,
        help_text='好友',
    )
    blocks = models.ManyToManyField(
        'self',
        related_name='blocked_by', verbose_name='黑名单',
        symmetrical=False, blank=True,
        help_text='黑名单',
    )

    def __str__(self):
        return self.name


class Report(models.Model):

    class Meta:
        verbose_name        = '举报'
        verbose_name_plural = '举报'

    id           = models.AutoField(verbose_name='ID', help_text='ID', primary_key=True)
    reporter     = models.ForeignKey(Player, models.CASCADE, related_name='reports', verbose_name='举报者', help_text='举报者')
    suspect      = models.ForeignKey(Player, models.CASCADE, related_name='reported_by', verbose_name='嫌疑人', help_text='嫌疑人')
    reason       = models.CharField('原因', max_length=10, help_text='原因')
    detail       = models.TextField('详情', help_text='原因')
    game_id      = models.IntegerField('游戏ID', null=True, blank=True, help_text='游戏ID')
    reported_at  = models.DateTimeField('举报时间', default=timezone.now, help_text='举报时间')
    outcome      = models.CharField('处理结果', max_length=150, blank=True, null=True, help_text='处理结果')

    def __str__(self):
        return f'{self.reporter.name} 举报 {self.suspect.name} {self.reason}'
