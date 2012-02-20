import gevent
import gevent.hub
from gevent.event import Event
import os
import threading
import functools
import thread

class ITIHub013(gevent.hub.Hub):
    '''gevent.hub.Hub with Inter-thread Interrupt support
       for gevent 0.13.x
    '''

    def __init__(self):
        gevent.hub.Hub.__init__(self)
        self.reqlist = []
        self.lock = threading.RLock()
        self.hub_tid = thread.get_ident()
        from gevent import core
        self.fd = os.pipe()
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

class ITIHub10(gevent.hub.Hub):
    '''gevent.hub.Hub with Inter-thread Interrupt support
       for gevent 1.0
    '''

    def __init__(self):
        gevent.hub.Hub.__init__(self)
        self.reqlist = []
        self.lock = threading.RLock()
        self.hub_tid = thread.get_ident()
        from gevent import core
        a = core.async(self.loop)
        a.start(self._iticallback)
        self.async_watcher = a

    def _iticallback(self):
        with self.lock:
            l = self.reqlist
            self.reqlist = []
        for cb in l:
            cb()

    def interrupt(self, cb, *args, **kwargs):
        f = functools.partial(cb, *args, **kwargs)
        with self.lock:
            self.reqlist.append(f)
        self.async_watcher.send()
        
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
    if not self.dead:
        self.parent = gevent.getcurrent()
        self.throw()

gevent.Greenlet.instant_kill = _instantkill

def patch_gevent_hub():
    global the_hub, ITIHub
    if hasattr(gevent.hub, 'set_hub'): # gevent 1.0
        ITIHub = ITIHub10
        the_hub = ITIHub()
        gevent.hub.set_hub(the_hub)
    else:
        ITIHub = ITIHub013
        gevent.hub._threadlocal.Hub = ITIHub # gevent 0.13

    the_hub = gevent.hub.get_hub()
    assert isinstance(the_hub, ITIHub), 'failed'
