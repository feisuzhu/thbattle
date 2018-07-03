# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.db import models

# -- own --


# -- code --
class Version(models.Model):

    class Meta:
        verbose_name        = '游戏版本'
        verbose_name_plural = '游戏版本'

    id = models.SlugField('版本', max_length=20, primary_key=True, help_text='版本')
    url = models.FileField('更新文件', help_text='更新文件')
    testing = models.BooleanField('显示测试服入口', default=False, help_text='显示测试服入口')

    def __str__(self):
        return self.id


class Setting(models.Model):

    class Meta:
        verbose_name        = '全局设置'
        verbose_name_plural = '全局设置'

    key     = models.SlugField('键', max_length=50, primary_key=True)
    value   = models.CharField('值', max_length=200)

    def __str__(self):
        return self.key


class News(models.Model):

    class Meta:
        verbose_name        = '新闻'
        verbose_name_plural = '新闻'

    id   = models.AutoField(primary_key=True)
    text = models.TextField('正文', help_text='正文')

    def __str__(self):
        return f'News({self.id})'
