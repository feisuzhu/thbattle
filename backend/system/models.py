# -*- coding: utf-8 -*-

# -- stdlib --
import datetime

# -- third party --
import pytz

# -- own --
# -- errord --
from django.db import models


# -- code --
_ = lambda s: {'help_text': s, 'verbose_name': s}


class Server(models.Model):

    class Meta:
        verbose_name        = '服务器'
        verbose_name_plural = '服务器'

    id      = models.AutoField(primary_key=True)
    name    = models.CharField(**_('名称'), max_length=20)
    version = models.IntegerField(**_('兼容客户端版本'))
    url     = models.CharField(**_('服务器地址'), max_length=200)  # tcp://cngame.thbattle.net:9999
    branch  = models.CharField(**_('Git 分支'), max_length=20)  # production
    chat    = models.CharField(**_('聊天服务'), max_length=200)

    def __str__(self):
        return str(self.id)


class SMSVerification(models.Model):

    class Meta:
        verbose_name        = '短信验证'
        verbose_name_plural = '短信验证'

    id       = models.AutoField(primary_key=True)
    key      = models.CharField(**_('验证 Key'), max_length=200, unique=True)
    time     = models.DateTimeField(**_('创建时间'), auto_now_add=True)
    phone    = models.CharField(**_('手机号'), max_length=20, null=True, blank=True)
    used     = models.BooleanField(**_('已使用'), default=False)

    def is_valid(self):
        return self.phone and not self.used and \
            datetime.datetime.now(pytz.utc) - self.time < datetime.timedelta(hours=1)

    def __str__(self):
        return f'[#{self.id}] {self.phone} {self.used}'


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
