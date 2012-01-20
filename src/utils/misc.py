import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from gevent import Greenlet
import types

class DataHolder(object):
    def __data__(self):
        return self.__dict__

class PlayerList(list):
    def __getattribute__(self, name):
        if hasattr(self[0], name):
            a = getattr(self[0], name)
            if type(a) == types.FunctionType:
                print 'delegate %s!' % name
                def wrapper(*args, **kwargs):
                    for p in self:
                        f = p.getattr(name)
                        f(*args, **kwargs)
                return wrapper
        return list.__getattribute__(self, name)

    def exclude(self, elem):
        return PlayerList(
            p for p in self if p is not elem
        )

    #def gexpect_any(self, _): pass
