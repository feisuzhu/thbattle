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

class ITIEvent(Event):
    '''
    Event can be set in other threads
    '''

    def set(self):
        assert isinstance(the_hub, ITIHub), 'not ITIHub'
        if the_hub.hub_tid == thread.get_ident():
            return Event.set(self)
        else:
            the_hub.interrupt(Event.set, self)

def _instantkill(self):
    # All Greenlets in gevent has a parent of the Hub,
    # if call throw directly, when Greenlet finishes execution,
    # Hub is switched to, cause current Greenlet
    # left unscheduled forever.
    # change the parent and get the CPU first time!
    self.parent = gevent.getcurrent()
    self.throw()

gevent.hub._threadlocal.Hub = ITIHub
the_hub = gevent.hub.get_hub()
assert isinstance(the_hub, ITIHub), 'failed'

gevent.Greenlet.instant_kill = _instantkill
