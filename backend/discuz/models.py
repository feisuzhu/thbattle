# -*- coding: utf-8 -*-

# -- stdlib --

# -- third party --
from django.db import models

# -- own --
import authext.models

# -- code --

class ForumMember(models.Model):
    uid      = models.AutoField("UID", primary_key=True, help_text="UID")
    username = models.CharField("昵称", unique=True, max_length=15, help_text="昵称")
    password = models.CharField("密码", max_length=32, default="", help_text="密码")
    email    = models.CharField("邮箱", max_length=40, help_text="邮箱")
    salt     = models.CharField("盐", max_length=6, help_text="盐")
    drops    = models.IntegerField("逃跑数", default=0, help_text="逃跑数")
    games    = models.IntegerField("游戏数", default=0, help_text="游戏数")
    jiecao   = models.IntegerField("节操", default=0, help_text="节操")
    migrated = models.BooleanField("是否已迁移", default=False, help_text="是否已迁移")

    user = models.OneToOneField(
        authext.models.User,
        models.CASCADE,
        help_text='论坛账号',
        verbose_name='论坛账号',
        unique=True,
        null=True,
        blank=True,
        related_name='forum_member'
    )

    @classmethod
    def find(cls, id):
        try:
            uid = int(id)
            uid = uid if uid < 500000 else None
        except ValueError:
            uid = None

        if uid is not None:
            return cls.objects.filter(uid=uid).first()
        return (
            cls.objects.filter(username=id).first()
            or cls.objects.filter(email=id).first()
        )
