# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from player.models import Player
from django.db import models

# -- own --


# -- code --
class Guild(models.Model):

    class Meta:
        verbose_name        = '势力'
        verbose_name_plural = '势力'

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        '名称',
        max_length=20,
        unique=True,
        help_text='名称',
    )
    leader = models.OneToOneField(Player,
        models.CASCADE,
        unique=True,
        related_name='leading_guild',
        verbose_name='领袖',
        help_text='领袖',
    )
    slogan = models.CharField('口号', max_length=200, help_text='口号')
    totem = models.ImageField('图腾', blank=True, help_text='图腾')
    badges = models.ManyToManyField(
        'badge.Badge',
        related_name='guilds',
        verbose_name='勋章',
        help_text='勋章',
    )
    requests = models.ManyToManyField(
        'player.Player',
        related_name='requested_guilds',
        verbose_name='申请列表',
        help_text='申请列表',
    )
    founded_at = models.DateTimeField('创建日期', auto_now_add=True, help_text='创建日期')

    def __str__(self):
        return self.name
