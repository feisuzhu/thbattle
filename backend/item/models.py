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
        verbose_name        = '道具'
        verbose_name_plural = '道具'

    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        Player, models.CASCADE,
        related_name='items',
        verbose_name='所有者',
        help_text='所有者',
    )
    type = models.SlugField('类型', max_length=20, help_text='类型')  # some-item:arg
    count = models.PositiveIntegerField('数量', help_text='数量')

    def __str__(self):
        return f'[{self.id}] {self.type}:{self.arg}'

'''
class ItemActivity(models.Model):

    class Meta:
        verbose_name        = '道具动作历史'
        verbose_name_plural = '道具动作历史'

    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(
        Player, models.CASCADE, related_name='+',
        verbose_name='相关用户', help_text='相关用户',
    )
    action = models.SlugField('动作', max_length=20, help_text='动作')
    item = models.ForeignKey(
        Item, models.CASCADE, related_name='activities',
        verbose_name='道具', help_text='道具',
    )
    extra = models.CharField('额外数据', max_length=256, help_text='额外数据')
    created_at = models.DateTimeField('日期', auto_now_add=True, help_text='日期')

    def __str__(self):
        return self.id
'''


class Exchange(models.Model):

    class Meta:
        verbose_name        = '交易中的道具'
        verbose_name_plural = '交易中的道具'

    id = models.AutoField(primary_key=True)
    seller = models.ForeignKey(
        Player, models.CASCADE, related_name='exchanges',
        verbose_name='卖家', help_text='卖家',
    )
    type = models.SlugField('类型', max_length=20, help_text='类型')  # some-item:arg
    price = models.PositiveIntegerField('价格', help_text='价格')

    def __str__(self):
        return f'[{self.id}] {self.item.type}'
