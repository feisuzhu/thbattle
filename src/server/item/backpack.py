# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import json

# -- third party --
# -- own --
from db.models import Item, ItemActivity
from db.session import transaction_with_retry
from game.base import GameItem
from server.item import helpers
from utils import exceptions


# -- code --
# test: ../tests/test_server_item.py


def use(uid, item_sku_or_id, is_consume=False):
    @transaction_with_retry
    def _use(s):
        if isinstance(item_sku_or_id, int):
            item = s.query(Item).filter(Item.owner_id == uid, Item.id == item_sku_or_id).first()
        else:
            item = s.query(Item).filter(Item.owner_id == uid, Item.sku == item_sku_or_id).first()

        if not item:
            raise exceptions.ItemNotFound

        s.add(ItemActivity(
            uid=uid, action='use', item_id=item.id,
            created=datetime.datetime.now(),
        ))

        if not is_consume:
            itemobj = GameItem.from_sku(item.sku)
            if not itemobj.usable:
                raise exceptions.ItemNotUsable

            itemobj.use(s, item.owner)

        item.status = 'used'
        item.owner_id = None


def consume(uid, item_sku_or_id):
    return use(uid, item_sku_or_id, is_consume=True)


def add(uid, item_sku, reason=None):
    @transaction_with_retry
    def id(s):
        helpers.require_free_backpack_slot(s, uid)

        item = Item(owner_id=uid, sku=item_sku, status='backpack')
        s.add(item)
        s.flush()

        s.add(ItemActivity(
            uid=uid, action='get', item_id=item.id,
            extra=reason and json.dumps(reason),
            created=datetime.datetime.now(),
        ))

        return item.id

    return id


def list(uid):
    @transaction_with_retry
    def items(s):
        items = s.query(Item) \
            .filter(Item.owner_id == uid, Item.status == 'backpack') \
            .order_by(Item.id.desc()) \
            .all()
        items = [{'id': i.id, 'sku': i.sku} for i in items]
        return items

    return items


def should_have(uid, sku):
    @transaction_with_retry
    def n(s):
        n = s.query(Item) \
            .filter(Item.owner_id == uid,
                    Item.status == 'backpack',
                    Item.sku == sku) \
            .count()
        return n

    if not n:
        raise exceptions.ItemNotFound

    return n


def drop(uid, item_id):
    @transaction_with_retry
    def id(s):
        item = s.query(Item) \
            .filter(Item.id == item_id) \
            .filter(Item.owner_id == uid) \
            .filter(Item.status == 'backpack') \
            .first()

        if not item:
            raise exceptions.ItemNotFound

        item.owner_id = None
        item.status = 'dropped'

        s.add(ItemActivity(
            uid=uid, action='drop', item_id=item.id,
            created=datetime.datetime.now(),
        ))

        return item.id

    return id
