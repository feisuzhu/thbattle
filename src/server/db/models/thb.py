# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

# -- own --
from server.db.base import Model


# -- code --
class Exchange(Model):
    __tablename__ = 'thb_exchange'

    id        = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('thb_user.id'), nullable=False)
    item_id   = Column(Integer, ForeignKey('thb_item.id'), nullable=False)
    price     = Column(Integer, nullable=False)

    item   = relationship('Item')
    seller = relationship('User')


class ItemActivity(Model):
    __tablename__ = 'thb_item_activity'

    id      = Column(Integer, primary_key=True)
    uid     = Column(Integer, ForeignKey('thb_user.id'), nullable=False)
    action  = Column(String(64), nullable=False)  # buy, sell, cancel_sell, use, get, lottery
    item_id = Column(Integer, ForeignKey('thb_item.id'), nullable=False)
    extra   = Column(String(256), nullable=True)
    created = Column(DateTime, nullable=False)

    item = relationship('Item')
    user = relationship('User')


class Item(Model):
    __tablename__ = 'thb_item'

    id       = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('thb_user.id'), index=True)
    sku      = Column(String(64), nullable=False)
    status   = Column(String(64), nullable=False)  # backpack, exchange, used

    owner = relationship('User')


class User(Model):
    __tablename__ = 'thb_user'

    # 节操放在论坛里了

    id       = Column(Integer, primary_key=True, autoincrement=False)
    name     = Column(String(128), nullable=False)  # cached, 论坛昵称
    ppoint   = Column(Integer, nullable=False)
    title    = Column(String(64), nullable=False)  # 称号, full-qualified-name
    showgirl = Column(Integer, ForeignKey('thb_showgirl.id'), nullable=False)  # 看板娘 id， or 0, foreign key to Showgirl.id


class Showgirl(Model):
    __tablename__ = 'thb_showgirl'

    id       = Column(Integer, primary_key=True)
    uid      = Column(Integer, nullable=False)
    girl_sku = Column(String(64), nullable=False)  # full-qualified-name
    mood     = Column(Integer, nullable=False)     # 心情，max 10，每天下降 1，摸一次头涨 2，每天一次
    last_pet = Column(DateTime, nullable=False)    # 上一次摸头
    food     = Column(Integer, nullable=False)     # 饥饿，max 30，每天下降1，喂一个物品涨 5 。

    # 两个都归零看板娘会跑掉！


class Unlocked(Model):
    __tablename__ = 'thb_unlocked'

    id       = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('thb_user.id'), nullable=False, index=True)
    type     = Column(String(64), nullable=False)  # achievement, character, skin, showgirl
    item     = Column(String(64), nullable=False)

    owner = relationship('User')
