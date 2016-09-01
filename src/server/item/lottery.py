# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import json
import random

# -- third party --
# -- own --
from account import Account
from db.models import Item, ItemActivity
from db.session import transactional, current_session
from server.item import constants, helpers
from utils import exceptions


# -- code --
# test: ../tests/test_server_item.py

@transactional('new')
def draw(uid, currency):
    s = current_session()
    u = Account.find(uid)
    if not u:
        raise exceptions.UserNotFound

    helpers.require_free_backpack_slot(s, uid)

    if currency == 'ppoint':
        amount = constants.LOTTERY_PRICE
        Account.add_user_credit(u, [('ppoint', -amount)],
                                exceptions.InsufficientFunds)

    elif currency == 'jiecao':
        amount = constants.LOTTERY_JIECAO_PRICE
        Account.add_user_credit(u, [('jiecao', -amount)],
                                exceptions.InsufficientFunds)

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
    return reward
