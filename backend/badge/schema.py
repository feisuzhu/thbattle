# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from graphene_django.types import DjangoObjectType

# -- own --
from . import models


# -- code --
class Badge(DjangoObjectType):
    class Meta:
        model = models.Badge


class PlayerBadge(DjangoObjectType):
    class Meta:
        model = models.PlayerBadge
