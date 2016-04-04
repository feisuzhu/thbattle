# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import json
import random

# -- third party --
# -- own --
from db.models import DiscuzMember, Item, ItemActivity, User
from db.session import Session
from server.item import constants, helpers
from utils import exceptions


# -- code --
# test: ../tests/test_server_item.py

def draw(uid, currency):
    try:
        s = Session()
        u = s.query(User).filter(User.id == uid).first()
        if not u:
            raise exceptions.UserNotFound

        helpers.require_free_backpack_slot(s, uid)

        if currency == 'ppoint':
            amount = constants.LOTTERY_PRICE
            if u.ppoint < amount:
                raise exceptions.InsufficientFunds

            u.ppoint -= amount

        elif currency == 'jiecao':
            amount = constants.LOTTERY_JIECAO_PRICE
            dz_member = s.query(DiscuzMember).filter(DiscuzMember.uid == uid).first()
            if not dz_member:
                raise exceptions.DiscuzUserNotFound

            if dz_member.member_count.jiecao < amount:
                raise exceptions.InsufficientFunds

            dz_member.member_count.jiecao -= amount

        else:
            raise exceptions.InvalidCurrency

        reward = random.choice(constants.LOTTERY_REWARD_LIST)

        item = Item(owner_id=uid, sku=reward, status='backpack')
        s.add(item)
        s.flush()
        s.add(ItemActivity(
            uid=uid, action='lottery', item_id=item.id,
            extra=json.dumps({'currency': currency, 'amount': amount}),
            created=datetime.datetime.now(),
        ))
        s.commit()
        return reward

    except:
        s.rollback()
        raise
