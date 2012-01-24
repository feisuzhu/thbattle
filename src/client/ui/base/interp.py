# -*- coding: utf-8 -*-

from time import time

class InterpDesc(object):
    def __init__(self, slot):
        self.slot = slot

    def __get__(self, obj, _type):
        v = getattr(obj, self.slot)
        if isinstance(v, AbstractInterp):
            val = v.value
            if v.finished:
                setattr(obj, self.slot, val)
            return val
        else:
            return v

    def __set__(self, obj, val):
        setattr(obj, self.slot, val)

class AbstractInterp(object):
    pass

class SineInterp(AbstractInterp):

    def __init__(self, f, t, animtime=0.5):
        from math import pi
        self._from, self._to = f, t
        self.delta = t - f
        self.starttime = time()
        self.factor = pi/2 / animtime
        self.animtime = animtime
        self.finished = False

    def _get_val(self):
        elapsed = time() - self.starttime
        if elapsed > self.animtime:
            self.finished = True
            return self._to
        else:
            from math import sin
            return self._from + self.delta * sin(elapsed * self.factor)

    value = property(_get_val)

class FixedInterp(AbstractInterp):

    def __init__(self, val, animtime):
        self.finished = False
        self._value = val
        self.starttime = time()

    def _get_val(self):
        elapsed = time() - self.starttime
        if elapsed > self.animtime:
            self.finished = True
        return self._value

    value = property(_get_val)

class ChainInterp(AbstractInterp):
    def __init__(self, *interps):
        self.lastval = 0.0
        self.interps = list(interps)
        st = time()
        self.starttime = st
        self.finished = False
        cum = st
        for c in self.interps:
            c.starttime = cum
            cum += c.animtime

    def _get_val(self):
        l = self.interps
        while l:
            val = l[0].value
            self.lastval = val
            if l[0].finished:
                del l[0]
                continue
            else:
                break
        else:
            self.finished = True
            val = self.lastval
        return val

    value = property(_get_val)
