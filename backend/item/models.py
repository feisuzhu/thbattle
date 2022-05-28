# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.db import models

from player.models import Player

# -- own --


# -- code --
class Item(models.Model):

    class Meta:
        verbose_name        = '物品'
        verbose_name_plural = '物品'

        constraints = [
            models.UniqueConstraint(fields=['sku', 'owner'], name='per_player_uniq')
        ]

    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        Player, models.CASCADE,
        related_name='items',
        verbose_name='所有者',
        help_text='所有者',
    )
    sku = models.SlugField('类型', max_length=20, help_text='类型')  # some-item:arg
    count = models.PositiveIntegerField('数量', help_text='数量')

    def __str__(self):
        return f'[{self.id}] {self.sku}'


class ItemActivity(models.Model):

    class Meta:
        verbose_name        = '物品动作历史'
        verbose_name_plural = '物品动作历史'

    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(
        Player, models.CASCADE, related_name='+',
        verbose_name='相关用户', help_text='相关用户',
    )
    action = models.SlugField('动作', max_length=20, help_text='动作')  # use, buy, get
    sku = models.SlugField('类型', max_length=20, help_text='类型')  # some-item:arg
    count = models.IntegerField('数量', help_text='数量')  # -2, -1, 1, 2
    extra = models.CharField('额外数据', max_length=256, help_text='额外数据')
    created_at = models.DateTimeField('日期', auto_now_add=True, help_text='日期')

    def __str__(self):
        return self.id


class ShopItem(models.Model):

    class Meta:
        verbose_name        = '商店'
        verbose_name_plural = '商店'

    id = models.AutoField(primary_key=True)
    sku = models.SlugField('类型', max_length=20, help_text='类型')  # some-item:arg
    count = models.IntegerField('数量', help_text='数量')  # 1000
    currency = models.SlugField('货币', max_length=20, help_text='货币')
    price = models.IntegerField('售价', help_text='售价')

    def __str__(self):
        return self.id


# RELATED FILES:
# schema.py
# admin.py
