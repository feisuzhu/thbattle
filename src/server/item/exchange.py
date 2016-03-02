# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import json

# -- third party --
from sqlalchemy.orm import joinedload

# -- own --
from db.models import Exchange, Item, ItemActivity, User
from db.session import Session
from server.item import constants, helpers
from server.item.exceptions import InsufficientFunds, ItemNotFound, TooManySellingItems
from server.item.exceptions import UserNotFound


# -- code --
# test: ../tests/test_server_item.py


def buy(uid, entry_id):
    try:
        s = Session()

        u = s.query(User).filter(User.id == uid).first()
        if not u:
            raise UserNotFound

        entry = s.query(Exchange).filter(Exchange.id == entry_id).first()
        if not entry:
            raise ItemNotFound

        seller = entry.seller

        if u.ppoint < entry.price:
            raise InsufficientFunds

        helpers.require_free_backpack_slot(s, uid)

        u.ppoint -= entry.price
        seller.ppoint += entry.price

        item = entry.item

        s.add(ItemActivity(
            uid=uid, action='buy', item_id=entry.item.id,
            extra=json.dumps({'seller': seller.id, 'price': entry.price}),
            created=datetime.datetime.now(),
        ))

        item.owner_id = u.id
        item.status = 'backpack'

        s.delete(entry)

        s.commit()
    except:
        s.rollback()
        raise


def sell(uid, item_id, price):
    try:
        s = Session()
        item = s.query(Item).filter(Item.id == item_id, Item.owner_id == uid).first()
        if not item:
            raise ItemNotFound

        existing = s.query(Exchange).filter(Exchange.seller_id == uid).count()
        if existing > constants.MAX_SELLING_ITEMS:
            raise TooManySellingItems

        s.add(Exchange(
            seller_id=uid,
            item_id=item.id,
            price=price,
        ))

        s.add(ItemActivity(
            uid=uid, action='sell', item_id=item.id,
            extra=json.dumps({'price': price}),
            created=datetime.datetime.now(),
        ))

        item.status = 'exchange'
        item.owner_id = None

        s.commit()

    except:
        s.rollback()
        raise


def cancel_sell(uid, entry_id):
    try:
        s = Session()
        entry = s.query(Exchange).filter(
            Exchange.id == entry_id,
            Exchange.seller_id == uid,
        ).first()

        if not entry:
            raise ItemNotFound

        helpers.require_free_backpack_slot(s, uid)

        item = entry.item
        item.owner_id = uid
        item.status = 'backpack'

        s.add(ItemActivity(
            uid=uid, action='cancel_sell', item_id=entry.item.id,
            extra=json.dumps({'price': entry.price}),
            created=datetime.datetime.now(),
        ))

        s.delete(entry)
        s.commit()
    except:
        s.rollback()
        raise


def list():
    try:
        s = Session()

        l = s.query(Exchange).options(joinedload('item')).order_by(Exchange.id.desc())
        l = [{'id': i.id,
              'seller_id': i.seller_id,
              'item_id': i.item_id,
              'item_sku': i.item.sku,
              'price': i.price} for i in l]

        s.commit()
        return l
    except:
        s.rollback()
        raise
