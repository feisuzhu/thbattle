import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult
from gevent import Greenlet
from gevent_extension import ITIEvent
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

class BatchList(list):
    def __getattribute__(self, name):
        try:
            list_attr = list.__getattribute__(self, name)
            return list_attr
        except AttributeError:
            pass

        return list.__getattribute__(self, '__class__')(
            getattr(i, name) for i in self
        )

    def __call__(self, *a, **k):
        return list.__getattribute__(self, '__class__')(
            f(*a, **k) for f in self
        )

    def exclude(self, elem):
        nl = list.__getattribute__(self, '__class__')(self)
        nl.remove(elem)
        return nl

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

class ScissorBox(object):
    exc = Exception('ScissorBox Invalid')
    def __init__(self, con, x, y, w, h):
        ax, ay = con.abs_coords()
        self.box = (x+ax, y+ay, w, h)

    def __enter__(self):
        from utils import Rect
        from pyglet.gl import GLint, glGetIntegerv, GL_SCISSOR_BOX, glScissor
        ob = (GLint*4)()
        glGetIntegerv(GL_SCISSOR_BOX, ob)
        ob = list(ob)
        box = [int(i) for i in self.box]
        nb = Rect(*ob).intersect(Rect(*box))
        if nb:
            glScissor(nb.x, nb.y, nb.width, nb.height)
        self.ob, self.nb = ob, nb
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_value is self.exc:
            return True
        else:
            from pyglet.gl import glScissor
            glScissor(*self.ob)

    def break_if_invalid(self):
        if not self.nb:
            raise self.exc
