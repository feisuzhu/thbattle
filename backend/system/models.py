# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.db import models

# -- own --


# -- code --
class Server(models.Model):

    class Meta:
        verbose_name        = '服务器'
        verbose_name_plural = '服务器'

    id      = models.AutoField(primary_key=True)
    name    = models.CharField('名称', max_length=20, help_text='名称')
    version = models.IntegerField('兼容客户端版本', help_text='兼容客户端版本')
    url     = models.CharField('服务器地址', max_length=200, help_text='服务器地址')  # tcp://cngame.thbattle.net:9999
    branch  = models.CharField('Git 分支', max_length=20, help_text='Git 分支')  # production

    def __str__(self):
        return str(self.id)


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
