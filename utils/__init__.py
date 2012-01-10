import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from gevent import Greenlet
import types

from itihub import *

class PlayerList(list):
    def write(self, data):
        for p in self:
            p.write(data)
    
    def gwrite(self, data):
        for p in self:
            p.gwrite(data)

    #def gexpect_any(self, _): pass
    
class AsyncService(object):
    
    def __init__(self):
        self.request_queue = Queue(10)

    def __getattribute__(self, name):
        try:
            f = object.__getattribute__(self, 'service_' + name)
        except:
            return Greenlet.__getattribute__(self, name)
        
        def asyncservice_wrapper(*args, **kwargs):
            return gevent.spawn(f, *args, **kwargs)

        return asyncservice_wrapper

