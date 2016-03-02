# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -- own --
from db.base import Model
from utils import instantiate


# -- code --
import server.db.models  # noqa


@instantiate
class DBState(object):
    __slots__ = (
        'engine',
        'session_maker',
    )

# Session = None


def init(db):
    global Session
    engine = create_engine(db, encoding='utf-8', convert_unicode=True)
    Model.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    DBState.engine = engine
    DBState.session_maker = Session
