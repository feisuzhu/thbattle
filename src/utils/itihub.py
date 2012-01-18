import gevent
import gevent.hub
from gevent.event import Event
import os
import threading
import functools
import thread

class ITIHub(gevent.hub.Hub):
    '''gevent.hub.Hub with Inter-thread Interrupt support'''

    def __init__(self):
        gevent.hub.Hub.__init__(self)
        self.fd = os.pipe()
        self.reqlist = []
        self.lock = threading.RLock()
        self.hub_tid = thread.get_ident()
        from gevent import core
        core.read_event(self.fd[0], self._iticallback, persist=True)

    def _iticallback(self, ev, evtype):
        os.read(self.fd[0], 100)
        with self.lock:
            l = self.reqlist
            self.reqlist = []
        for cb in l:
            cb()

    def interrupt(self, cb, *args, **kwargs):
        f = functools.partial(cb, *args, **kwargs)
        with self.lock:
            self.reqlist.append(f)
        os.write(self.fd[1], ' ')

    def get_hub(self):
        return self

    @staticmethod
    def replace_default():
        gevent.hub._threadlocal.Hub = ITIHub
        hub = gevent.hub.get_hub()
        assert isinstance(hub, ITIHub), 'failed'
        ITIHub.the_hub = hub

class ITIEvent(Event):
    '''
    Event can be set in other threads
    '''

    def set(self):
        if ITIHub.the_hub.hub_tid == thread.get_ident():
            return Event.set(self)
        else:
            ITIHub.the_hub.interrupt(Event.set, self)
