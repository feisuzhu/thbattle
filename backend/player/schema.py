# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
from django.db import transaction
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
import graphene as gh

# -- own --
from . import models
from authext.schema import User
from utils.graphql import require_login, require_perm
from discuz.models import ForumMember
from discuz.auth import check_password


# -- code --
class Player(DjangoObjectType):
    class Meta:
        model = models.Player
        exclude = [
            'friended_by',
            'blocked_by',
            'reported_by',
        ]

    friend_requests = gh.List(
        gh.NonNull('player.schema.Player'),
        description="未处理的好友请求",
    )

    @staticmethod
    def resolve_friends(root, info):
        ctx = info.context
        require_login(ctx)
        p = ctx.api_user.player
        if p.id != root.id:
            require_perm(ctx, 'player.view_player')
        return root.friends.filter(friends__id=root.id)

    @staticmethod
    def resolve_friend_requests(root, info):
        ctx = info.context
        require_login(ctx)
        p = ctx.api_user.player
        if p.id != root.id:
            require_perm(ctx, 'player.view_player')
        return root.friended_by.exclude(
            id__in=root.friends.only('id')
        )

    user = gh.Field(User, description="关联用户")

    @staticmethod
    def resolve_user(root, info):
        ctx = info.context
        require_login(ctx)
        u = ctx.api_user
        if u.id == root.user.id or require_perm(ctx, 'player.view_user'):
            return root.user

    badges = gh.List(gh.NonNull('badge.schema.PlayerBadge'), description='玩家的勋章')

    @staticmethod
    def resolve_badges(root, info):
        from badge.models import PlayerBadge
        return PlayerBadge.objects.filter(player__id=root.id)

    power = gh.Int(description="P")

    @staticmethod
    def resolve_power(root, info):
        # TODO
        return 233


class Report(DjangoObjectType):
    class Meta:
        model = models.Report


class Availability(gh.ObjectType):
    phone = gh.Boolean(phone=gh.String(description="手机号"), description="手机号可用")
    name = gh.Boolean(name=gh.String(description="昵称"), description="昵称可用")

    @classmethod
    def Field(cls, **kw):
        return gh.Field(
            Availability,
            resolver=cls.resolve,
            **kw,
        )

    @staticmethod
    def resolve(root, info):
        return Availability()

    @staticmethod
    def resolve_phone(root, info, phone):
        if not models.is_phone_number(phone):
            raise GraphQLError('手机号不合法')

        from authext.models import PhoneLogin
        return not PhoneLogin.objects.filter(phone=phone.strip()).exists()

    @staticmethod
    def resolve_name(root, info, name):
        if not models.is_name(name):
            raise GraphQLError('昵称不合法')

        return not models.Player.objects.filter(name=name.strip()).exists()


class PlayerQuery(gh.ObjectType):

    player = gh.Field(
        Player,
        id=gh.Int(description="玩家ID"),
        name=gh.String(description="玩家昵称"),
        token=gh.String(description="用户token"),
        description="获取玩家",
    )

    @staticmethod
    def resolve_player(root, info, id=None, forum_id=None, name=None, token=None):
        if id is not None:
            return models.Player.objects.get(id=id)
        elif name is not None:
            return models.Player.objects.get(name=name.strip())
        elif token is not None:
            from authext.models import User
            if id := User.uid_from_token(token):
                return models.Player.objects.get(id=id)

        return None

    # players = gh.List(
    #     gh.NonNull(Player),
    #     keyword=gh.String(description="关键字"),
    #     description="查找玩家",
    # )

    # @staticmethod
    # def resolve_players(root, info, keyword):
    #     return models.Player.objects.filter(name__contains=keyword)

    availability = Availability.Field(description="查询是否被占用")


class Register(gh.Mutation):
    class Arguments:
        sms_verification_key = gh.String(required=True, description="短信验证 Key")

    token  = gh.String(required=True, description="登录令牌")
    user   = gh.Field(User, required=True, description="用户")
    player = gh.Field(Player, required=True, description="玩家")

    @staticmethod
    def mutate(root, info, sms_verification_key):
        from system.models import SMSVerification
        r = SMSVerification.objects.filter(key=sms_verification_key).first()
        if not (r and r.can_use()):
            raise GraphQLError('短信验证未通过')

        from authext.models import PhoneLogin, User
        if PhoneLogin.objects.filter(phone=r.phone).exists():
            raise GraphQLError('手机已经注册')

        with transaction.atomic():
            r.used = True
            r.save()
            u = User.objects.create_user(username=f'm{r.phone}', password=hex(random.getrandbits(128))[2:])
            u.save()
            PhoneLogin.objects.create(user=u, phone=r.phone).save()
            models.Player.objects.create(
                user=u,
                name=f'萌新{random.randrange(100000000, 999999999)}',
                avatar='http://img.thbattle.cn/avatars/kedama.png',
            ).save()

        return Register(
            user=u, player=u.player,
            token=u.token(),
        )


class Update(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Field(
            Player,
            bio=gh.String(description="签名"),
            avatar=gh.String(description="头像"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, bio=None, avatar=None):
        ctx = info.context
        require_login(ctx)
        p = ctx.api_user.player
        p.bio = bio or p.bio
        p.avatar = avatar or p.avatar
        p.save()
        return p


class BindForum(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            account=gh.String(description="账号"),
            password=gh.String(description="密码"),
            migrate_name=gh.Boolean(description="是否迁移昵称"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, account, password, migrate_name):
        ctx = info.context
        require_login(ctx)

        if m := ctx.api_user.forum_member:
            if m.migrated:
                raise GraphQLError('不可以重复绑定')

        m = ForumMember.find(account)
        if not m:
            raise GraphQLError('该用户不存在')

        plain = password.encode('utf-8')
        hash  = m.password.encode('utf-8')
        salt  = m.salt.encode('utf-8')
        if not check_password(plain, hash, salt):
            raise GraphQLError('密码错误')

        if m.migrated:
            raise GraphQLError('该用户已迁移')


        # TODO: Issue badge
        p = ctx.api_user.player
        p.forum_member = m
        if migrate_name:
            p.name = m.username
        p.games = m.games
        p.drops = m.drops
        p.save()

        m.migrated = True
        m.save()

        return True


class Friend(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            id=gh.Int(required=True, description="目标玩家ID"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, id):
        ctx = info.context
        require_login(ctx)
        me = ctx.api_user.player
        p = models.Player.objects.get(id=id)
        if not p:
            raise GraphQLError('找不到相应的玩家')
        me.friends.add(p)
        return True


class Unfriend(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            id=gh.Int(required=True, description="目标玩家ID"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, id):
        ctx = info.context
        require_login(ctx)
        me = ctx.api_user.player
        p = models.Player.objects.get(id=id)
        if not p:
            raise GraphQLError('找不到相应的玩家')
        me.friends.remove(p)
        p.friends.remove(me)
        return True


class Block(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            id=gh.Int(required=True, description="目标玩家ID"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, id):
        ctx = info.context
        require_login(ctx)
        me = ctx.api_user.player
        tgt = models.Player.objects.get(id=id)
        if not tgt:
            raise GraphQLError('没有找到指定的玩家')

        me.blocks.add(tgt)
        return True


class Unblock(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            id=gh.Int(required=True, description="目标玩家ID"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, id):
        ctx = info.context
        require_login(ctx)
        me = ctx.api_user.player
        tgt = models.Player.objects.get(id=id)
        if not tgt:
            raise GraphQLError('没有找到指定的玩家')

        me.remove.add(tgt)
        return True


class ReportOp(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Field(
            Report,
            id=gh.Int(required=True, description="目标玩家ID"),
            reason=gh.String(required=True, description="举报原因"),
            detail=gh.String(required=True, description="详情"),
            game_id=gh.Int(description="游戏ID（如果有）"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, id, reason, detail, game_id=None):
        ctx = info.context
        require_login(ctx)
        me = ctx.api_user.player
        tgt = models.Player.objects.get(id=id)
        if not tgt:
            raise GraphQLError('没有找到指定的玩家')

        r = models.Report.objects.create(
            reporter=me, suspect=tgt,
            reason=reason, detail=detail, game_id=game_id,
        )

        r.save()
        return r


class AddCredit(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Field(
            Player,
            id=gh.Int(required=True, description="目标玩家ID"),
            jiecao=gh.Int(description="节操"),
            games=gh.Int(description="游戏数"),
            drops=gh.Int(description="逃跑数"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, id, jiecao=0, games=0, drops=0):
        ctx = info.context
        require_perm(ctx, 'player.change_credit')
        p = models.Player.objects.get(id=id)
        p.jiecao += jiecao
        p.games += games
        p.drops += drops
        p.save()
        return p


class UpdatePrefs(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            prefs=gh.String(required=True, description="偏好(msgpack+base64)"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, prefs):
        ctx = info.context
        require_login(ctx)
        p = ctx.api_user.player
        p.prefs = prefs
        p.save()
        return p


class PlayerOps(gh.ObjectType):
    PlRegister    = Register.Field(description="注册")
    PlUpdate      = Update.Field(description="更新资料")
    PlBindForum   = BindForum.Field(description="绑定论坛帐号")
    PlUpdatePrefs = UpdatePrefs.Field(description="更新个人偏好")

    PlFriend   = Friend.Field(description="发起好友请求")
    PlUnfriend = Unfriend.Field(description="移除好友/拒绝好友请求")

    PlBlock   = Block.Field(description="拉黑")
    PlUnblock = Unblock.Field(description="解除拉黑")
    PlReport  = ReportOp.Field(description="举报玩家")

    PlAddCredit = AddCredit.Field(description="增加积分（服务器用）")
