import gevent
import gevent.hub
from gevent.event import Event
import os, sys
import threading
import functools
import thread

#from ctypes import *

# This file are pure hacks, and, fuck Windows!!!!!!!!!

class BaseITIHub(gevent.hub.Hub):
    '''gevent.hub.Hub with Inter-thread Interrupt support
    '''

    def __init__(self):
        gevent.hub.Hub.__init__(self)
        self.reqlist = []
        self.lock = threading.RLock()
        self.hub_tid = thread.get_ident()

        self.register_event()

    def _iticallback(self, *args):
        self.clear_event()
        with self.lock:
            l = self.reqlist
            self.reqlist = []
        for cb in l:
            cb()

    def interrupt(self, cb, *args, **kwargs):
        f = functools.partial(cb, *args, **kwargs)
        with self.lock:
            self.reqlist.append(f)
        self.set_event()

class ITIHub013Win_DOESNOTWORK(BaseITIHub):
    def register_event(self):
        from gevent import core
        kn32 = windll.kernel32
        i, o = c_int(), c_int()
        if not kn32.CreatePipe(byref(i), byref(o), 0, 0):
            raise Exception('Failed to create pipe')
        self.fd = (i.value, o.value)
        core.read_event(self.fd[0], self._iticallback, persist=True)

    def set_event(self):
        o = self.fd[1]
        kn32 = windll.kernel32
        nbytes = c_int()
        kn32.WriteFile(o, byref(nbytes), 1, byref(nbytes), 0)

    def clear_event(self):
        i = self.fd[0]
        kn32 = windll.kernel32
        nbytes = c_int()
        kn32.WriteFile(i, byref(nbytes), 100, byref(nbytes), 0)

class ITIHub013Win(BaseITIHub):
    def __init__(self):
        BaseITIHub.__init__(self)
        self.signal = False

    def register_event(self):
        pass

    def set_event(self):
        self.signal = True

    def clear_event(self):
        self.signal = False

class ITIHub013Unix(BaseITIHub):
    def register_event(self):
        self.fd = os.pipe()
        from gevent import core
        core.read_event(self.fd[0], self._iticallback, persist=True)

    def set_event(self):
        os.write(self.fd[1], ' ')

    def clear_event(self):
        os.read(self.fd[0], 100)

class ITIHub10(BaseITIHub):
    '''gevent.hub.Hub with Inter-thread Interrupt support
       for gevent 1.0
    '''

    def register_event(self):
        from gevent import core
        a = core.async(self.loop)
        a.start(self._iticallback)
        self.async_watcher = a

    def set_event(self):
        self.async_watcher.send()

    def clear_event(self):
        pass

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
    import sys
    if hasattr(gevent.hub, 'set_hub'): # gevent 1.0
        ITIHub = ITIHub10
        the_hub = ITIHub()
        gevent.hub.set_hub(the_hub)
    else:
        if sys.platform == 'win32':
            ITIHub = ITIHub013Win
        else:
            ITIHub = ITIHub013Unix
        gevent.hub._threadlocal.Hub = ITIHub # gevent 0.13

    the_hub = gevent.hub.get_hub()
    assert isinstance(the_hub, ITIHub), 'failed'

    if sys.platform == 'win32':
        # ITIHub013Win part 2
        def polling():
            while True:
                gevent.sleep(0.1)
                if the_hub.signal:
                    the_hub._iticallback()
        gevent.spawn(polling)

def hub_interrupt(cb):
    global the_hub
    the_hub.interrupt(cb)
