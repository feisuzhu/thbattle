# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import json

# -- third party --
# -- own --
from db.models import Item, ItemActivity
from db.session import Session
from server.item import helpers, items
from server.item.exceptions import ItemNotFound, ItemNotUsable


# -- code --
# test: ../tests/test_server_item.py


def use(uid, item_sku_or_id, is_consume=False):
    try:
        s = Session()
        if isinstance(item_sku_or_id, int):
            item = s.query(Item).filter(Item.owner_id == uid, Item.id == item_sku_or_id).first()
        else:
            item = s.query(Item).filter(Item.owner_id == uid, Item.sku == item_sku_or_id).first()

        if not item:
            raise ItemNotFound

        s.add(ItemActivity(
            uid=uid, action='use', item_id=item.id,
            created=datetime.datetime.now(),
        ))

        if not is_consume:
            itemobj = items.from_sku(item.sku)
            if not itemobj.usable:
                raise ItemNotUsable

            itemobj.use(s, item.owner)

        item.status = 'used'
        item.owner_id = None
        s.commit()

    except:
        s.rollback()
        raise


def consume(uid, item_sku_or_id):
    return use(uid, item_sku_or_id, is_consume=True)


def add(uid, item_sku, reason=None):
    try:
        s = Session()

        helpers.require_free_backpack_slot(s, uid)

        item = Item(owner_id=uid, sku=item_sku, status='backpack')
        s.add(item)
        s.flush()

        s.add(ItemActivity(
            uid=uid, action='get', item_id=item.id,
            extra=reason and json.dumps(reason),
            created=datetime.datetime.now(),
        ))

        s.commit()

        return item.id

    except:
        s.rollback()
        raise


def list(uid):
    try:
        s = Session()
        items = s.query(Item) \
            .filter(Item.owner_id == uid, Item.status == 'backpack') \
            .order_by(Item.id.desc()) \
            .all()
        items = [{'id': i.id, 'sku': i.sku} for i in items]
        s.commit()
        return items
    except:
        s.rollback()
        raise


def drop(uid, item_id):
    try:
        s = Session()
        item = s.query(Item) \
            .filter(Item.id == item_id) \
            .filter(Item.owner_id == uid) \
            .filter(Item.status == 'backpack') \
            .first()

        if not item:
            raise ItemNotFound

        item.owner_id = None
        item.status = 'dropped'

        s.add(ItemActivity(
            uid=uid, action='drop', item_id=item.id,
            created=datetime.datetime.now(),
        ))

        s.commit()

        return item.id

    except:
        s.rollback()
        raise
