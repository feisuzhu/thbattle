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

class BatchList(list):
    def __getattribute__(self, name):
        cls = list.__getattribute__(self, '__class__')

        try:
            list_attr = list.__getattribute__(self, name)
            return list_attr
        except AttributeError:
            pass

        if len(self):
            a = getattr(self[0], name)
            if type(a) in (types.FunctionType, types.MethodType):
                return lambda *a, **k: cls(
                    getattr(p, name)(*a, **k) for p in self
                )
            else:
                return cls(
                    getattr(i, name) for i in self
                )

    def exclude(self, elem):
        cls = list.__getattribute__(self, '__class__')
        return cls(
            p for p in self if p is not elem
        )

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
