# -*- coding: utf-8 -*-

import baseclasses as bc

import logging
log = logging.getLogger('UI_Interp')

def getinterp(obj, name):
    desc = getattr(obj.__class__, name)
    slot = desc.slot
    return getattr(obj, slot)

class InterpDesc(object):
    def __init__(self, slot):
        self.slot = slot

    def __get__(self, obj, _type):
        if obj is None:
            # class get
            return self
        v = getattr(obj, self.slot)
        if isinstance(v, AbstractInterp):
            val = v.value
            if v.finished:
                setattr(obj, self.slot, val)
                if v.on_done:
                    v.on_done(obj, self)
            return val
        else:
            return v

    def __set__(self, obj, val):
        setattr(obj, self.slot, val)

    def __delete__(self, obj):
        setattr(obj, self.slot, None)

class AbstractInterp(object):
    pass

class FunctionInterp(AbstractInterp):
    def __init__(self, f, t, animtime, on_done=None):
        from math import pi
        self._from, self._to = f, t
        self.delta = t - f
        self.starttime = bc.current_time
        self.animtime = animtime
        self.finished = False
        self.on_done = on_done

    def _get_val(self):
        elapsed = bc.current_time - self.starttime
        if elapsed > self.animtime:
            self.finished = True
            return self._to
        else:
            return self._from + self.delta * self.func(elapsed / self.animtime)

    value = property(_get_val)

from math import sin, cos, pi
class LinearInterp(FunctionInterp):
    def func(self, percent):
        return percent

class SineInterp(FunctionInterp):
    def func(self, percent):
        return sin(percent*pi/2)

class CosineInterp(FunctionInterp):
    def func(self, percent):
        return 1 - cos(percent*pi/2)

class FixedInterp(AbstractInterp):

    def __init__(self, val, animtime, on_done=None):
        self.finished = False
        self._value = val
        self.starttime = bc.current_time
        self.animtime = animtime
        self.on_done = on_done

    def _get_val(self):
        elapsed = bc.current_time - self.starttime
        if elapsed > self.animtime:
            self.finished = True
        return self._value

    value = property(_get_val)

class ChainInterp(AbstractInterp):
    def __init__(self, *interps, **k):
        self.lastval = 0.0
        self.on_done = k.get('on_done')
        self.interps = list(interps)
        st = bc.current_time
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
