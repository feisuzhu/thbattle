# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
from urllib.parse import unquote

# -- third party --
from django.db import transaction
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
import django.contrib.auth as auth
import django.contrib.auth.models as auth_models
import graphene as gh

# -- own --
from . import models
from utils.graphql import require_login, require_perm
import utils.leancloud


# -- code --
class User(DjangoObjectType):
    class Meta:
        model = models.User
        exclude_fields = [
            'password',
        ]


class Group(DjangoObjectType):
    class Meta:
        model = auth_models.Group


class Permission(DjangoObjectType):
    class Meta:
        model = auth_models.Permission


class Player(DjangoObjectType):
    class Meta:
        model = models.Player
        exclude_fields = [
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
        p = ctx.user.player
        if p.id != root.id:
            require_perm(ctx, 'player.view_player')
        return root.friends.filter(friends__id=root.id)

    @staticmethod
    def resolve_friend_requests(root, info):
        ctx = info.context
        require_login(ctx)
        p = ctx.user.player
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
        u = ctx.user
        if u.id == root.user.id or require_perm(ctx, 'player.view_user'):
            return root.user

    token = gh.String(description="登录令牌")

    @staticmethod
    def resolve_token(root, info):
        ctx = info.context
        require_login(ctx)
        p = ctx.user.player
        if p.id != root.id:
            require_perm(ctx, 'superuser')

        return root.token()


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

        return not models.User.objects.filter(phone=phone.strip()).exists()

    @staticmethod
    def resolve_name(root, info, name):
        if not models.is_name(name):
            raise GraphQLError('昵称不合法')

        return not models.Player.objects.filter(name=name.strip()).exists()


class PlayerQuery(gh.ObjectType):
    user = gh.Field(
        User,
        id=gh.Int(description="用户ID"),
        phone=gh.String(description="手机号"),
        description="获取用户",
    )

    @staticmethod
    def resolve_user(root, info, id=None, phone=None):
        ctx = info.context
        require_perm(ctx, 'player.view_user')

        if id is not None:
            return models.User.objects.get(id=id)
        elif phone is not None:
            return models.User.objects.get(phone=phone.strip())

        return None

    me = gh.Field(User, description="当前登录用户")

    @staticmethod
    def resolve_me(root, info):
        u = info.context.user
        return u if u.is_authenticated else None

    player = gh.Field(
        Player,
        id=gh.Int(description="玩家ID"),
        forum_id=gh.Int(description="论坛ID"),
        name=gh.String(description="玩家昵称"),
        token=gh.String(description="登录令牌"),
        description="获取玩家",
    )

    @staticmethod
    def resolve_player(root, info, id=None, forum_id=None, name=None, token=None):
        if id is not None:
            return models.Player.objects.get(id=id)
        elif id is not None:
            return models.Player.objects.get(forum_id=forum_id)
        elif name is not None:
            return models.Player.objects.get(name=name.strip())
        elif token is not None:
            return models.Player.from_token(token)

        return None

    players = gh.List(
        gh.NonNull(Player),
        keyword=gh.String(description="关键字"),
        description="查找玩家",
    )

    @staticmethod
    def resolve_players(root, info, keyword):
        return models.Player.objects.filter(name__contains=keyword)

    token = gh.String(description="获取登录令牌")

    @staticmethod
    def resolve_token(root, info):
        req = info.context
        u = req.user
        if u.is_authenticated:
            return u.token()
        else:
            return None

    availability = Availability.Field(description="查询是否被占用")


class Register(gh.Mutation):
    class Arguments:
        name     = gh.String(required=True, description="昵称")
        phone    = gh.String(required=True, description="手机")
        password = gh.String(required=True, description="密码")
        smscode  = gh.Int(required=True, description="短信验证码")

    token  = gh.String(required=True, description="登录令牌")
    user   = gh.Field(User, required=True, description="用户")
    player = gh.Field(Player, required=True, description="玩家")

    @staticmethod
    def mutate(root, info, name, phone, password, smscode):
        name, phone = map(str.strip, [name, phone])

        if not models.is_phone_number(phone):
            raise GraphQLError('手机号不合法')

        if not models.is_name(name):
            raise GraphQLError('昵称不合法')

        if models.User.objects.filter(phone=phone).exists():
            raise GraphQLError('手机已经注册')
        elif models.Player.objects.filter(name=name).exists():
            raise GraphQLError('昵称已经注册')
        elif not utils.leancloud.verify_smscode(phone, smscode):
            raise GraphQLError('验证码不正确')

        with transaction.atomic():
            u = models.User.objects.create_user(phone=phone, password=password)
            u.save()
            p = models.Player.objects.create(user=u, name=name)
            p.save()

        return Register(
            user=u, player=u.player,
            token=u.token(),
        )


class Login(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Field(
            User,
            phone=gh.String(description="手机"),
            forum_id=gh.Int(description="论坛用户ID"),
            name=gh.String(description="昵称"),
            password=gh.String(required=True, description="密码"),
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info, phone=None, forum_id=None, name=None, password=None):
        phone = phone and phone.strip()
        name = name and name.strip()

        if name:
            p = models.Player.objects.get(name=name.strip())
            if not p:
                return None
            phone = p.user.phone
        elif forum_id:
            p = models.Player.objects.get(forum_id=forum_id)
            if not p:
                return None
            phone = p.user.phone
        elif phone:
            pass
        else:
            return None

        u = auth.authenticate(phone=phone, password=password)
        if not u:
            return None

        auth.login(info.context, u)
        return u


class Logout(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info):
        auth.logout(info.context)
        return True


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
        p = ctx.user.player
        p.bio = bio or p.bio
        p.avatar = avatar or p.avatar
        p.save()
        return p


class BindForum(object):
    @classmethod
    def Field(cls, **kw):
        return gh.Boolean(
            resolver=cls.mutate,
            **kw,
        )

    @staticmethod
    def mutate(root, info):
        from backend.settings import ForumInterconnect as F
        import discuz.auth as dzauth
        import pymysql
        from urllib.parse import urlparse, parse_qsl
        from utils.piper import one, Q
        ctx = info.context
        require_login(ctx)
        p = ctx.user.player
        if p.forum_id:
            raise GraphQLError('不可以重复绑定')

        cookies = {
            k.split('_')[-1]: v for k, v in ctx.COOKIES.items()
            if k.startswith(F.COOKIEPRE)
        }

        if not ('auth' in cookies and 'saltkey' in cookies):
            raise GraphQLError('需要先登录论坛')

        auth = unquote(cookies['auth'])
        saltkey = unquote(cookies['saltkey'])

        decoded = dzauth.decode_cookie(auth, F.AUTHKEY, saltkey)
        if 'uid' not in decoded:
            raise GraphQLError('需要先登录论坛')

        url = urlparse(F.DB)
        db = pymysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],
            port=int(url.port or 3306),
            **dict(parse_qsl(url.query)),
        )

        rst = Q(db, '''
            -- SQL
            SELECT
                m.username as name,
                c.extcredits2 as jiecao,
                c.extcredits7 as drops,
                c.extcredits8 as games
            FROM
                pre_ucenter_members m,
                pre_common_member_count c
            WHERE
                m.uid = c.uid AND m.uid = :uid
        ''', {'uid': decoded['uid']}) | one

        del db

        p.forum_id = decoded['uid']
        p.forum_name = rst['name']
        p.jiecao = rst['jiecao']
        p.games = rst['games']
        p.drops = rst['drops']

        p.save()

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
        me = ctx.user.player
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
        me = ctx.user.player
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
        me = ctx.user.player
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
        me = ctx.user.player
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
        me = ctx.user.player
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


class PlayerOps(gh.ObjectType):
    login      = Login.Field(description="登录")
    logout     = Logout.Field(description="退出登录")
    register   = Register.Field(description="注册")
    update     = Update.Field(description="更新资料")
    bind_forum = BindForum.Field(description="绑定论坛帐号")
    friend     = Friend.Field(description="发起好友请求")
    unfriend   = Unfriend.Field(description="移除好友/拒绝好友请求")
    block      = Block.Field(description="拉黑")
    unblock    = Unblock.Field(description="解除拉黑")
    report     = ReportOp.Field(description="举报玩家")
    add_credit = AddCredit.Field(description="增加积分（服务器用）")
