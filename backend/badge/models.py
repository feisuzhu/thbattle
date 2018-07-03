# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.db import models

# -- own --
# -- code --


class Badge(models.Model):

    class Meta:
        verbose_name        = '勋章'
        verbose_name_plural = '勋章'

    id          = models.AutoField(primary_key=True)
    title       = models.CharField('标题', max_length=50, unique=True, help_text='标题')
    description = models.CharField('描述', max_length=200, help_text='描述')
    icon        = models.ImageField('图标', help_text='图标')
    icon2x      = models.ImageField('图标@2x', help_text='图标@2x')

    def __str__(self):
        return self.title
