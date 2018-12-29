# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
import graphene as gh

# -- own --
from graphql import GraphQLError
from django.core.cache import caches


# -- code --
def stub(cls, desc):
    return gh.Field(
        cls,
        resolver=lambda root, info: cls(),
        description=desc,
    )


def require_perm(ctx, perm):
    u = ctx.user
    if not u.has_perm(perm):
        raise GraphQLError('没有权限')

    return True


def rate_limit(token: str, duration: float) -> None:
    c = caches['default']

    if c.get(token):
        raise GraphQLError('请求过于频繁')

    c.set(token, 'rate_limit', duration)

    return True


def require_login(ctx):
    u = ctx.user
    if not u.is_authenticated:
        raise GraphQLError('需要登录')

    return True


class Paging(gh.InputObjectType):
    offset   = gh.Int()
    limit    = gh.Int()
    order_by = gh.String()
    token    = gh.String()

    def get_order_by(self, avail):
        order = self.order_by
        if order in avail or f'-{order}' in avail:
            return avail
        else:
            return avail[0]
