# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from server.item.exceptions import InvalidItemSKU
from server.db.models import DiscuzMember, User


# -- code --
ITEMS = {}


def item(cls):
    ITEMS[cls.key] = cls
    return cls


def from_sku(sku):
    if ':' in sku:
        key, args = sku.split(':')
        args = args.split(',')
    else:
        key = sku
        args = []

    if key not in ITEMS:
        raise InvalidItemSKU

    cls = ITEMS[key]
    if len(cls.args) != len(args):
        raise InvalidItemSKU

    try:
        args = [T(v) for T, v in zip(cls.args, args)]
    except:
        raise InvalidItemSKU

    return cls(*args)


# -----
@item
class Foo(object):
    key, args, usable, title = 'foo', [], True, 'Foo'
    description = u'没什么用，测试用的'
    use = lambda *a: 0


@item
class Bar(object):
    key, args, usable, title = 'bar', [], False, 'Bar'
    description = u'没什么用，测试用的'


@item
class Jiecao(object):
    key    = 'jiecao'
    args   = [int]
    usable = True

    def __init__(self, amount):
        self.amount = amount

    @property
    def title(self):
        return u'%s点节操' % self.amount

    @property
    def description(self):
        return u'打包的%s点节操，使用后你的节操会增加。可以放在交易所出售。' % self.amount

    def use(self, session, user):
        dz_member = session.query(DiscuzMember).filter(DiscuzMember.uid == user.id).first()
        dz_member.member_count.jiecao += self.amount


@item
class PPoint(object):
    key    = 'ppoint'
    args   = [int]
    usable = True

    def __init__(self, amount):
        self.amount = amount

    @property
    def title(self):
        return u'%s个P点' % self.amount

    @property
    def description(self):
        return u'打包的%s个P点，使用后你的P点会增加。尽管可以放在交易所出售但是好像没啥意义。' % self.amount

    def use(self, session, user):
        user.ppoint += self.amount
