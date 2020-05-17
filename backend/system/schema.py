# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.core.cache import caches
from graphene_django.types import DjangoObjectType
import graphene as gh

# -- own --
from . import models
from utils.graphql import rate_limit
import utils.leancloud


# -- code --
class Server(DjangoObjectType):
    class Meta:
        model = models.Server


class News(DjangoObjectType):
    class Meta:
        model = models.News


class Setting(DjangoObjectType):
    class Meta:
        model = models.Setting


# ------------------------
class SystemQuery(gh.ObjectType):
    servers = gh.List(
        gh.NonNull(Server),
        description="获取服务器列表",
        required=True,
    )

    @staticmethod
    def resolve_servers(root, info):
        return models.Server.objects.all()

    setting = gh.String(
        key=gh.String(required=True),
        description="获取全局设置",
    )

    @staticmethod
    def resolve_setting(root, info, key):
        r = models.Setting.objects.get(key=key)
        return r and r.value

    news = gh.String(description="获取当前新闻")

    @staticmethod
    def resolve_news(root, info):
        r = models.News.objects.order_by('-id').first()
        return r.text if r else ''

    game_id = gh.Int(required=True, description="分配游戏ID")

    @staticmethod
    def resolve_game_id(root, info):
        c = caches['default']
        c.get_or_set('next_game_id', lambda: 0)
        return c.incr('next_game_id')


class SystemOps(gh.ObjectType):
    sms_code = gh.Boolean(
        phone=gh.String(required=True, description="手机号"),
        description="请求验证码",
    )

    @staticmethod
    def resolve_sms_code(root, info, phone):
        rate_limit(f"sms-code:ip:{info.context.META['REMOTE_ADDR']}", 60)
        rate_limit(f"sms-code:phone:{phone}", 60)
        utils.leancloud.send_smscode(phone)
        return True
