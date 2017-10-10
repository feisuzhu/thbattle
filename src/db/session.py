# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random
from functools import wraps

# -- third party --
from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from gevent.local import local

# -- own --
from db.base import Model
from utils import instantiate

# -- code --
import db.models  # noqa


@instantiate
class DBState(object):
    __slots__ = (
        'engine',
        'session_maker',
    )

Session = None

current = local()


def init(connstr, drop_first=False):
    global Session
    engine = create_engine(
        connstr,
        encoding='utf-8',
        convert_unicode=True,
        echo=False,
        isolation_level='SERIALIZABLE',
    )
    drop_first and Model.metadata.drop_all(engine)
    Model.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    DBState.engine = engine
    DBState.session_maker = Session


def current_session():
    return current.__dict__.setdefault('session', None)


def transactional(session=None, isolation_level=None, retry=5):
    def wrap(f):
        @wraps(f)
        def wrapper(*a, **k):
            lsession = session
            osession = current_session()

            if lsession is None:
                lsession = osession or 'new'

            if lsession != 'new':
                r = 1
            else:
                r = retry

            if isolation_level is not None and 'sqlite' not in DBState.engine.name:
                session_factory = lambda: Session(
                    bind=DBState.engine.execution_options(
                        isolation_level=isolation_level))
            else:
                session_factory = Session

            try:
                for n in xrange(r):
                    s = lsession if lsession != 'new' else session_factory()
                    current.session = s

                    try:
                        ret = f(*a, **k)
                        if lsession == 'new':
                            s.commit()
                        return ret
                    except BaseException, e:
                        s.rollback()

                        # Retry when PyMySQL dead lock
                        if isinstance(e, DBAPIError):
                            from pymysql.err import DatabaseError

                            if isinstance(e.orig, DatabaseError):
                                errno = e.orig.args[0]

                                if errno == 1213 and n + 1 < r:
                                    import gevent
                                    gevent.sleep(0.001 * pow(2, n) + random.random() * 0.003)
                                    continue

                        raise
            finally:
                current.session = osession

        return wrapper
    return wrap


@transactional('new')
def transaction_with_retry(f):
    return f(current_session())
