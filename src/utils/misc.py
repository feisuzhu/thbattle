import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from gevent import Greenlet
from itihub import ITIEvent
import types

class DataHolder(object):
    def __data__(self):
        return self.__dict__

    @staticmethod
    def parse(dd):
        for k, v in dd.items():
            if isinstance(v, dict):
                setattr(self, k, DataHolder.parse(v))
            elif isinstance(v, (list, tuple, set, frozenset)):
                setattr(self, k, type(v)(
                    DataHolder.parse(lv) if isinstance(lv, dict) else lv
                    for lv in v
                ))
            else:
                setattr(self, k, v)

class PlayerList(list):
    def __getattribute__(self, name):
        from game.autoenv import Game
        if hasattr(Game.player_class, name):
            a = getattr(Game.player_class, name)
            if type(a) in (types.FunctionType, types.MethodType):
                def wrapper(*args, **kwargs):
                    for p in self:
                        f = getattr(p, name)
                        f(*args, **kwargs)
                return wrapper
        return list.__getattribute__(self, name)

    def exclude(self, elem):
        return PlayerList(
            p for p in self if p is not elem
        )

    #def gexpect_any(self, _): pass

class IRP(object):
    '''I/O Request Packet'''
    def __init__(self):
        e = ITIEvent()
        e.clear()
        self.event = e

    def complete(self):
        self.event.set()

    def wait(self):
        self.event.wait()
