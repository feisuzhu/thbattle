# -*- coding: utf-8 -*-

from time import time

class SineInterpolation(object):

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

class Fixed(object):

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

class ChainInterpolation(object):
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
