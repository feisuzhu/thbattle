import gevent
import gevent.hub
from gevent.event import Event
import os
import threading
import functools
import thread

from utils import DataHolder

class ITIHub(gevent.hub.Hub):
    '''gevent.hub.Hub with Inter-thread Interrupt support'''

    def __init__(self):
        gevent.hub.Hub.__init__(self)
        i = DataHolder()
        i.fd = os.pipe()
        i.reqlist = []
        i.lock = threading.RLock()
        self._itidata = i
        from gevent import core
        core.read_event(i.fd[0], self._iticallback, persist=True)

    def _iticallback(self, ev, evtype):
        i = self._itidata
        os.read(i.fd[0], 100)
        with i.lock:
            l = i.reqlist
            i.reqlist = []
        for cb in l:
            cb()

    def interrupt(self, cb, *args, **kwargs):
        f = functools.partial(cb, *args, **kwargs)
        i = self._itidata
        with i.lock:
            i.reqlist.append(f)
        os.write(i.fd[1], ' ')
    
    @staticmethod
    def replace_default():
        gevent.hub._threadlocal.Hub = ITIHub
        assert isinstance(gevent.hub.get_hub(), ITIHub), 'failed'

class ITIEvent(Event):
    '''
    Event can be set in other threads
    '''
    
    def __init__(self):
        Event.__init__(self)
        self._tid = thread.get_ident()
        self._hub = gevent.hub.get_hub()

    def set(self):
        if self._tid == thread.get_ident():
            return Event.set(self)
        else:
            self._hub.interrupt(Event.set, self)
