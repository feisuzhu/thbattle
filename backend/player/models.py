# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import base64
import re

# -- third party --
from django.db import models
from django.utils import timezone
import django.contrib.auth.models as auth_models
import itsdangerous
import msgpack

# -- own --
import backend.settings


# -- code --
def is_phone_number(value):
    if not isinstance(value, str):
        return False

    return bool(re.match(r'^(?!17[01])\d{11}$', value))


def is_name(value):
    return bool(re.match(r'^[^\s%*"<>&]{3,15}$', value))


class UserManager(auth_models.BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        """
        Create and save a user with the given phone, and password.
        """
        if not phone:
            raise ValueError('必须填写手机')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone, password, **extra_fields)


class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    class Meta:
        verbose_name        = '用户'
        verbose_name_plural = '用户'

    USERNAME_FIELD = 'phone'

    objects = UserManager()

    phone = models.CharField('手机号', unique=True, max_length=15, validators=[is_phone_number], help_text='手机号')
    is_staff = models.BooleanField('职员状态', default=False, help_text='是否可以登录后台')
    is_active = models.BooleanField('启用帐号', default=True, help_text='指明用户是否被认为活跃的。以反选代替删除帐号。')
    date_joined = models.DateTimeField('加入日期', default=timezone.now, help_text='加入日期')


class Player(models.Model):

    class Meta:
        verbose_name        = '玩家'
        verbose_name_plural = '玩家'

        permissions = (
            ("change_credit", "可以修改积分"),
        )

    user       = models.OneToOneField(User, models.CASCADE, verbose_name='用户', help_text='关联用户')
    name       = models.CharField('昵称', unique=True, max_length=15, validators=[is_name], help_text='昵称')
    forum_id   = models.IntegerField('论坛ID', blank=True, null=True, unique=True, help_text='论坛ID')
    forum_name = models.CharField('论坛昵称', blank=True, null=True, max_length=150, unique=True, help_text='论坛昵称')
    bio        = models.CharField('签名', blank=True, max_length=150, help_text='签名')
    avatar     = models.URLField('头像', blank=True, max_length=150, help_text='头像')
    prefs      = models.TextField('个人设置', blank=True, help_text='个人设置')

    ppoint = models.IntegerField('P点', default=0, help_text='P点')
    jiecao = models.IntegerField('节操', default=0, help_text='节操')
    games  = models.IntegerField('游戏数', default=0, help_text='游戏数')
    drops  = models.IntegerField('逃跑数', default=0, help_text='逃跑数')

    guild = models.ForeignKey(
        'guild.Guild', models.SET_NULL,
        related_name='members', verbose_name='势力',
        blank=True, null=True,
        help_text='势力',
    )
    badges = models.ManyToManyField(
        'badge.Badge',
        related_name='players', verbose_name='勋章',
        blank=True,
        help_text='勋章',
    )
    friends = models.ManyToManyField(
        'self',
        related_name='friended_by', verbose_name='好友',
        symmetrical=False, blank=True,
        help_text='好友',
    )
    blocks = models.ManyToManyField(
        'self',
        related_name='blocked_by', verbose_name='黑名单',
        symmetrical=False, blank=True,
        help_text='黑名单',
    )

    token_signer = itsdangerous.TimestampSigner(backend.settings.SECRET_KEY)

    def token(self):
        data = base64.b64encode(msgpack.dumps({'player': True, 'id': self.id}))
        return self.token_signer.sign(data).decode('utf-8')

    @classmethod
    def from_token(cls, token, max_age=30):
        data = cls.token_signer.unsign(token.encode('utf-8'), max_age=max_age)
        data = msgpack.loads(base64.b64decode(data), encoding='utf-8')
        if data.get('player') is not True:
            return None

        return cls.objects.get(id=data['id'])

    def __str__(self):
        return self.name


class Report(models.Model):

    class Meta:
        verbose_name        = '举报'
        verbose_name_plural = '举报'

    reporter     = models.ForeignKey(Player, models.CASCADE, related_name='reports', verbose_name='举报者', help_text='举报者')
    suspect      = models.ForeignKey(Player, models.CASCADE, related_name='reported_by', verbose_name='嫌疑人', help_text='嫌疑人')
    reason       = models.CharField('原因', max_length=10, help_text='原因')
    detail       = models.TextField('详情', help_text='原因')
    game_id      = models.IntegerField('游戏ID', null=True, blank=True, help_text='游戏ID')
    reported_at  = models.DateTimeField('举报时间', default=timezone.now, help_text='举报时间')
    outcome      = models.CharField('处理结果', max_length=150, blank=True, null=True, help_text='处理结果')

    def __str__(self):
        return f'{self.reporter.name} 举报 {self.suspect.name} {self.reason}'
