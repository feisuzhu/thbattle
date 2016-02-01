# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from server.db.models import Item
from server.item import constants
from server.item.exceptions import BackpackFull


# -- code --
def require_free_backpack_slot(sess, uid):
    cnt = sess.query(Item).filter(Item.owner_id == uid).count()
    if cnt >= constants.BACKPACK_SIZE:
        raise BackpackFull
