# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

# -- own --
from db.base import Model


# -- code --
class Exchange(Model):
    __tablename__ = 'exchange'

    id        = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    item_id   = Column(Integer, ForeignKey('item.id'), nullable=False)
    price     = Column(Integer, nullable=False)

    item   = relationship('Item')
    seller = relationship('User')


class ItemActivity(Model):
    __tablename__ = 'item_activity'

    id      = Column(Integer, primary_key=True)
    uid     = Column(Integer, ForeignKey('user.id'), nullable=False)
    action  = Column(String(64), nullable=False)  # buy, sell, cancel_sell, use, get, lottery
    item_id = Column(Integer, ForeignKey('item.id'), nullable=False)
    extra   = Column(String(256), nullable=True)
    created = Column(DateTime, nullable=False)

    item = relationship('Item')
    user = relationship('User')


class Item(Model):
    __tablename__ = 'item'

    id       = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('user.id'), index=True)
    sku      = Column(String(64), nullable=False)
    status   = Column(String(64), nullable=False)  # backpack, exchange, used

    owner = relationship('User')


class User(Model):
    __tablename__ = 'user'

    id           = Column(Integer, primary_key=True, autoincrement=False)
    username     = Column(String(128), index=True, unique=True, nullable=False)  # 用户名，暂时与论坛同步
    password     = Column(String(128), nullable=False, default='')  # not used, for now.
    email        = Column(String(128), index=True, unique=True, nullable=False)  # 暂时与论坛同步
    status       = Column(Integer, nullable=False, default=0)  # 暂时与论坛同步
    ppoint       = Column(Integer, nullable=False, default=0)
    jiecao       = Column(Integer, nullable=False, default=0)  # not used, for now. see DiscuzMemberCount
    games        = Column(Integer, nullable=False, default=0)  # not used, for now. see DiscuzMemberCount
    drops        = Column(Integer, nullable=False, default=0)  # not used, for now. see DiscuzMemberCount
    title        = Column(String(128), nullable=False, default='')  # 称号, full-qualified-name
    lastactivity = Column(Integer, nullable=False, default=0)
    showgirl     = Column(Integer, ForeignKey('showgirl.id'), nullable=True)  # 看板娘 id， foreign key to Showgirl.id


class Showgirl(Model):
    __tablename__ = 'showgirl'

    id       = Column(Integer, primary_key=True)
    uid      = Column(Integer, nullable=False)
    girl_sku = Column(String(64), nullable=False)  # full-qualified-name
    mood     = Column(Integer, nullable=False)     # 心情，max 10，每天下降 1，摸一次头涨 2，每天一次
    food     = Column(Integer, nullable=False)     # 饥饿，max 30，每天下降1，喂一个物品涨 5 。

    # 两个都归零看板娘会跑掉！


class Unlocked(Model):
    __tablename__ = 'unlocked'

    id       = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    type     = Column(String(64), nullable=False)  # achievement, character, skin, showgirl
    item     = Column(String(64), nullable=False)

    owner = relationship('User')
