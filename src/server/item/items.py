# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from utils import extendclass
from game.item import Jiecao, PPoint


# -- code --
class JiecaoServerSide(Jiecao):
    __metaclass__ = extendclass

    usable = True

    def use(self, session, user):
        from db.models import DiscuzMember
        dz_member = session.query(DiscuzMember).filter(DiscuzMember.uid == user.id).first()
        dz_member.member_count.jiecao += self.amount
        user.jiecao += self.amount


class PPointServerSide(PPoint):
    __metaclass__ = extendclass

    usable = True

    def use(self, session, user):
        user.ppoint += self.amount
