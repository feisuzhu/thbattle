# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from graphene_django.types import DjangoObjectType
import graphene as gh

# -- own --
from . import models


# -- code --
class FixedText(DjangoObjectType):
    class Meta:
        model = models.FixedText

    can_use = gh.Field(
        gh.NonNull(gh.Boolean),
        description='可以使用',
        pid=gh.Int(required=True, description='玩家ID'),
    )

    @staticmethod
    def resolve_can_use(root, info, pid):
        return hasattr(root, 'shared') or root.avail_to.filter(id=pid).exists()


class EmojiPack(DjangoObjectType):
    class Meta:
        model = models.EmojiPack

    can_use = gh.Field(
        gh.NonNull(gh.Boolean),
        description='可以使用',
        pid=gh.Int(required=True, description='玩家ID'),
    )

    @staticmethod
    def resolve_can_use(root, info, pid):
        return hasattr(root, 'shared') or root.avail_to.filter(id=pid).exists()


class Emoji(DjangoObjectType):
    class Meta:
        model = models.Emoji


class ChatQuery(gh.ObjectType):
    fixed_text = gh.Field(
        FixedText,
        id=gh.Int(required=True, description="定型文ID"),
        description="获取定型文",
    )

    @staticmethod
    def resolve_fixed_text(root, info, id):
        return models.FixedText.objects.filter(id=id).first()

    emoji_pack = gh.Field(
        EmojiPack,
        id=gh.Int(required=True, description="大表情包ID"),
        description="获取大表情包",
    )

    @staticmethod
    def resolve_emoji_pack(root, info, id):
        return models.EmojiPack.objects.filter(id=id).first()

    emoji = gh.Field(
        Emoji,
        id=gh.Int(required=True, description="大表情ID"),
        description="获取大表情",
    )

    @staticmethod
    def resolve_emoji(root, info, id):
        return models.Emoji.objects.filter(id=id).first()


class ChatOps(gh.ObjectType):
    pass
