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
        exclude = ['avail_to']

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


class EmojiPack(DjangoObjectType):
    class Meta:
        model = models.EmojiPack
        exclude = ['avail_to']

    can_use = gh.Field(
        gh.NonNull(gh.Boolean),
        description='可以使用',
        pid=gh.Int(required=True, description='玩家ID'),
    )

    @staticmethod
    def resolve_can_use(root, info, pid):
        return hasattr(root, 'shared') or root.avail_to.filter(id=pid).exists()



class ChatQuery(gh.ObjectType):
    fixed_texts = gh.List(
        gh.NonNull(FixedText),
        ids=gh.List(gh.NonNull(gh.Int), required=True, description="定型文ID"),
        required=True,
        description="获取定型文",
    )

    @staticmethod
    def resolve_fixed_texts(root, info, ids):
        return models.FixedText.objects.filter(id__in=ids)

    emoji_packs = gh.List(
        gh.NonNull(EmojiPack),
        ids=gh.List(gh.NonNull(gh.Int), required=True, description="大表情包ID"),
        required=True,
        description="获取大表情包",
    )

    @staticmethod
    def resolve_emoji_packs(root, info, ids):
        return models.EmojiPack.objects.filter(id__in=ids)

    emojis = gh.List(
        gh.NonNull(Emoji),
        ids=gh.List(gh.NonNull(gh.Int), required=True, description="大表情ID"),
        required=True,
        description="获取大表情",
    )

    @staticmethod
    def resolve_emojis(root, info, ids):
        return models.Emoji.objects.filter(id__in=ids)


class ChatOps(gh.ObjectType):
    pass
