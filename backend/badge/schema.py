# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

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
