# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
from graphene_django import DjangoObjectType
from graphql import GraphQLError
import django.contrib.auth as auth
import django.contrib.auth.models as auth_models
import graphene as gh

# -- own --
from . import models
from utils.graphql import require_perm


# -- code --
class User(DjangoObjectType):
    class Meta:
        model = auth_models.User
        exclude = [
            'password',
        ]

    token = gh.String(description="登录令牌")

    @staticmethod
    def resolve_token(root, info):
        # from backend import debug
        # rv = debug.state.collect_current()
        # print(f'http://localhost:8000/.debug/console/{rv["id"]}')
        return root.token()


class Group(DjangoObjectType):
    class Meta:
        model = auth_models.Group


class Permission(DjangoObjectType):
    class Meta:
        model = auth_models.Permission


class Login(gh.ObjectType):
    phone = gh.Field(
        User,
        sms_verification_key=gh.String(required=True, description="验证码"),
        description="手机登录",
    )

    @staticmethod
    def resolve_phone(root, info, sms_verification_key):
        from system.models import SMSVerification

        verify = SMSVerification.objects.filter(key=sms_verification_key).first()
        if verify.can_use():
            phone = models.PhoneLogin.objects.filter(phone=verify.phone).first()
            if not phone:
                return None
            verify.used = True
            verify.save()
            return phone.user
        else:
            raise GraphQLError("验证码无效")

    token = gh.Field(
        User,
        token=gh.String(required=True, description="令牌"),
        description="令牌登录",
    )

    @staticmethod
    def resolve_token(root, info, token):
        if user := auth.authenticate(token=token):
            return user

        return None

    account = gh.Field(
        User,
        account=gh.String(required=True, description="账号"),
        password=gh.String(required=True, description="密码"),
        description="帐号密码登录",
    )

    @staticmethod
    def resolve_account(root, account, password):
        if user := auth.authenticate(username=account, password=password):
            return user
        else:
            raise GraphQLError("帐号或密码错误")

        return None


class UserQuery(gh.ObjectType):
    user = gh.Field(
        User,
        id=gh.Int(required=True, description="用户ID"),
        description="获取用户",
    )

    @staticmethod
    def resolve_user(root, info, id):
        ctx = info.context
        require_perm(ctx, 'player.view_user')
        return models.User.objects.filter(id=id).first()

    login = gh.Field(Login, description="登录")

    def resolve_login(root, info):
        return Login()


class UserOps(gh.ObjectType):
    pass
