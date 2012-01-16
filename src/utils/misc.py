import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from gevent import Greenlet
import types

class DataHolder(object):
    def __data__(self):
        return self.__dict__

class PlayerList(list):
    def write(self, data):
        for p in self:
            p.write(data)
    
    def gwrite(self, data):
        for p in self:
            p.gwrite(data)

    #def gexpect_any(self, _): pass
