# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from utils import exceptions


# -- code --
class GameItem(object):
    inventory = {}

    key  = None
    args = []

    @classmethod
    def register(cls, item_cls):
        assert issubclass(item_cls, cls)
        cls.inventory[item_cls.key] = item_cls
        return cls

    @classmethod
    def from_sku(cls, sku):
        if ':' in sku:
            key, args = sku.split(':')
            args = args.split(',')
        else:
            key = sku
            args = []

        if key not in cls.inventory:
            raise exceptions.InvalidItemSKU

        cls = cls.inventory[key]
        if len(cls.args) != len(args):
            raise exceptions.InvalidItemSKU

        try:
            args = [T(v) for T, v in zip(cls.args, args)]
        except:
            raise exceptions.InvalidItemSKU

        return cls(*args)

    @property
    def title(self):
        return u'ITEM-TITLE'

    @property
    def description(self):
        return u'ITEM-DESC'


# ------
@GameItem.register
class Jiecao(GameItem):
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
        from db.models import DiscuzMember
        dz_member = session.query(DiscuzMember).filter(DiscuzMember.uid == user.id).first()
        dz_member.member_count.jiecao += self.amount
        user.jiecao += self.amount


@GameItem.register
class PPoint(GameItem):
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
