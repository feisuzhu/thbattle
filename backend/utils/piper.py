# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import functools
import itertools
import re

# -- third party --
# -- own --


# -- code --
class Piper(object):
    def __init__(self, f):
        self.f = f

    def __ror__(self, arg):
        return self.f(arg)

    def __call__(self, arg):
        return self.f(arg)

    @classmethod
    def make(cls, f):
        return cls(f)


@Piper.make
def rows(c):
    rst = c.fetchall()
    c.close()
    return rst


@Piper.make
def row(c):
    rst = c.fetchone()
    c.close()
    return rst


@Piper.make
def flatted(c):
    rst = [i[0] for i in c]
    c.close()
    return rst


@Piper.make
def array(c):
    colnames = next(zip(*c.description))
    rst = [dict(zip(itertools.cycle(colnames), i)) for i in c.fetchall()]
    c.close()
    return rst


@Piper.make
def mapping(c):
    assert len(c.description) == 2
    rst = dict(c)
    c.close()
    return rst


@Piper.make
def one(c):
    colnames = next(zip(*c.description))
    row = c.fetchone()
    if not row:
        return None

    c.close()
    return dict(zip(itertools.cycle(colnames), row))


@Piper.make
def scalar(c):
    row = c.fetchone()
    if not row:
        return None

    c.close()
    return row[0]


@Piper.make
def rowcount(c):
    return c.rowcount


_sql_trans = functools.partial(re.compile(r'(?<=[ (\[]):([a-z][a-z0-9_-]*)').sub, r'%(\1)s')


def Q(db, sql, *args):
    c = db.cursor()
    c.execute(_sql_trans(sql), *args)
    return c
