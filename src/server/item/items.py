# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from utils import extendclass
from game.items import Jiecao, PPoint
from account import Account


# -- code --
class JiecaoServerSide(Jiecao):
    __metaclass__ = extendclass

    usable = True

    def use(self, session, user):
        Account.add_user_credit(user, [('jiecao', self.amount)])


class PPointServerSide(PPoint):
    __metaclass__ = extendclass

    usable = True

    def use(self, session, user):
        Account.add_user_credit(user, [('ppoint', self.amount)])
