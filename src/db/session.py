# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random

# -- third party --
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -- own --
from db.base import Model
from utils import instantiate
import pymysql


# -- code --
import db.models  # noqa


@instantiate
class DBState(object):
    __slots__ = (
        'engine',
        'session_maker',
    )

Session = None


def init(connstr):
    global Session
    engine = create_engine(connstr, encoding='utf-8', convert_unicode=True)
    Model.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    DBState.engine = engine
    DBState.session_maker = Session


def transaction_with_retry(f):
    # for PyMySQL

    for n in xrange(5):
        try:
            s = Session()
            ret = f(s)
            s.commit()
            return ret
        except pymysql.err.DatabaseError as e:
            s.rollback()
            if e.errno == 1213 and n < 5:
                import gevent
                gevent.sleep(0.001 * pow(2, n) + random.random() * 0.003)
                continue
            else:
                raise
        except:
            s.rollback()
            raise
