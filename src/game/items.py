# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --
# -- own --
from game.base import GameItem
from account import Account

# -- code --
log = logging.getLogger('game.items')


@GameItem.register
class Jiecao(GameItem):
    key    = 'jiecao'
    args   = [int]
    usable = True

    def init(self, amount):
        self.amount = amount

    @property
    def title(self):
        return u'%s点节操' % self.amount

    @property
    def description(self):
        return u'打包的%s点节操，使用后你的节操会增加。可以放在交易所出售。' % self.amount

    def use(self, session, user):
        Account.add_user_credit(user, [('jiecao', self.amount)])


@GameItem.register
class PPoint(GameItem):
    key    = 'ppoint'
    args   = [int]
    usable = True

    def init(self, amount):
        self.amount = amount

    @property
    def title(self):
        return u'%s个P点' % self.amount

    @property
    def description(self):
        return u'打包的%s个P点，使用后你的P点会增加。尽管可以放在交易所出售但是好像没啥意义。' % self.amount

    def use(self, session, user):
        Account.add_user_credit(user, [('ppoint', self.amount)])
