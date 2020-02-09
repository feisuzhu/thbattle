# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import deque
from contextlib import contextmanager
from functools import wraps
from time import time
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple, Type, TypeVar
from weakref import WeakSet
import functools
import logging
import re

# -- third party --
from gevent.lock import Semaphore
from gevent.queue import Queue
import gevent

# -- own --

# -- code --
log = logging.getLogger('util.misc')
dbgvals: Dict[str, object] = {}


class ObjectDict(dict):
    __slots__ = ()

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError

    def __setattr__(self, k, v):
        self[k] = v

    @classmethod
    def parse(cls, data):
        if isinstance(data, dict):
            return cls({k: cls.parse(v) for k, v in data.items()})
        elif isinstance(data, (list, tuple, set, frozenset)):
            return type(data)([cls.parse(v) for v in data])

        return data


T = TypeVar('T')


class BatchList(List[T]):
    __slots__ = ()

    def __getattribute__(self, name):
        try:
            list_attr = list.__getattribute__(self, name)
            return list_attr
        except AttributeError:
            pass

        return BatchList(
            getattr(i, name) for i in self
        )

    def __call__(self, *a, **k):
        return BatchList(
            f(*a, **k) for f in self
        )

    '''
    @typing.overload
    def __getitem__(self, i: int) -> T: ...

    @typing.overload
    def __getitem__(self, s: slice) -> 'BatchList[T]': ...

    def __getitem__(self, a):
        if isinstance(a, slice):
            return BatchList(list.__getitem__(self, a))
        else:
            return list.__getitem__(self, a)
    '''

    def exclude(self, elem: T) -> 'BatchList[T]':
        nl = BatchList(self)
        try:
            nl.remove(elem)
        except ValueError:
            pass

        return nl

    def rotate_to(self, elem: T) -> 'BatchList[T]':
        i = self.index(elem)
        n = len(self)
        return self.__class__((self*2)[i:i+n])

    def replace(self, old: T, new: T) -> bool:
        try:
            self[self.index(old)] = new
            return True
        except ValueError:
            return False

    def find_replace(self, pred: Callable[[T], bool], new: T) -> bool:
        for i, v in enumerate(self):
            if pred(v):
                self[i] = new
                return True
        else:
            return False

    def sibling(self, me: T, offset=1) -> T:
        i = self.index(me)
        n = len(self)
        return self[(i + offset) % n]


def remove_dups(s):
    seen: Set[Any] = set()
    for i in s:
        if i not in seen:
            yield i
            seen.add(i)


def classmix(*_classes) -> type:
    classes: Any = []
    for c in _classes:
        if hasattr(c, '_is_mixedclass'):
            classes.extend(c.__bases__)
        else:
            classes.append(c)

    classes = tuple(remove_dups(classes))
    cached = cls_cache.get(classes, None)
    if cached: return cached

    clsname = ', '.join(cls.__name__ for cls in classes)
    new_cls = type('Mixed(%s)' % clsname, classes, {'_is_mixedclass': True})
    cls_cache[classes] = new_cls
    return new_cls


cls_cache: Dict[tuple, type] = {}


def hook(module):
    def inner(hooker):
        funcname = hooker.__name__
        hookee = getattr(module, funcname)

        @wraps(hookee)
        def real_hooker(*args, **kwargs):
            return hooker(hookee, *args, **kwargs)
        setattr(module, funcname, real_hooker)
        return real_hooker
    return inner


def extendclass(clsname, bases, _dict):
    for cls in bases:
        for key, value in _dict.items():
            if key == '__module__':
                continue
            setattr(cls, key, value)


def partition(pred: Callable[[Any], bool], lst: Iterable[Any]) -> Tuple[List[Any], List[Any]]:
    f: List[Any]
    t: List[Any]
    f, t = [], []
    for i in lst:
        (f, t)[pred(i)].append(i)

    return t, f


def track(f):
    @functools.wraps(f)
    def _wrapper(*a, **k):
        print('%s: %s %s' % (f.__name__, a, k))
        return f(*a, **k)
    return _wrapper


def flatten(l):
    rst = []

    def _flatten(sl):
        for i in sl:
            if isinstance(i, (list, tuple, deque)):
                _flatten(i)
            else:
                rst.append(i)

    _flatten(l)
    return rst


def group_by(l, keyfunc):
    if not l: return []

    grouped = []
    group = []

    lastkey = keyfunc(l[0])
    for i in l:
        k = keyfunc(i)
        if k == lastkey:
            group.append(i)
        else:
            grouped.append(group)
            group = [i]
            lastkey = k

    if group:
        grouped.append(group)

    return grouped


def instantiate(cls):
    return cls()


def surpress_and_restart(f):
    def wrapper(*a, **k):
        while True:
            try:
                return f(*a, **k)
            except Exception as e:
                import logging
                log = logging.getLogger('misc')
                log.exception(e)

    return wrapper


def swallow(f):
    def wrapper(*a, **k):
        try:
            return f(*a, **k)
        except Exception:
            pass

    return wrapper


def log_failure(logger):
    def decorate(f):
        def wrapper(*a, **k):
            try:
                return f(*a, **k)
            except Exception as e:
                logger.exception(e)
                raise

        return wrapper

    return decorate


class ObservableEvent(object):
    listeners: Set[Callable]

    def __init__(self, weakref=False):
        self.listeners = WeakSet() if weakref else set()

    def __iadd__(self, ob):
        self.listeners.add(ob)
        return self

    def __isub__(self, ob):
        self.listeners.discard(ob)
        return self

    def notify(self, *a, **k):
        for ob in list(self.listeners):
            ob(*a, **k)


class GenericPool(object):
    def __init__(self, factory, size, container_class=Queue):
        self.factory = factory
        self.size = size
        self.container = container_class(size)
        self.inited = False

    def __call__(self):
        @contextmanager
        def manager():
            container = self.container

            if not self.inited:
                for i in range(self.size):
                    container.put(self.factory())

                self.inited = True

            try:
                item = container.get()
                yield item
            except Exception:
                item = self.factory()
                raise
            finally:
                try:
                    container.put_nowait(item)
                except Exception:
                    pass

        return manager()


def debounce(seconds):
    def decorate(f):
        lock = Semaphore(1)
        last = None

        def bouncer(fire, *a, **k):
            nonlocal last
            gevent.sleep(seconds)
            last = None
            fire and f(*a, **k)

        @wraps(f)
        def wrapper(*a, **k):
            nonlocal last
            rst = lock.acquire(blocking=False)
            if not rst:
                return

            try:
                run = False
                if last is None:
                    last = gevent.spawn(bouncer, False)
                    run = True
                else:
                    last.kill()
                    last = gevent.spawn(bouncer, True, *a, **k)
            finally:
                lock.release()

            run and f(*a, **k)

        wrapper.__name__ == f.__name__
        return wrapper

    return decorate


class ThrottleState(object):
    __slots__ = ('running', 'pending', 'args')

    running: bool
    pending: bool
    args: Tuple[tuple, dict]

    def __init__(self):
        self.running = self.pending = False


def throttle(seconds: float) -> Callable[[T], T]:
    def decorate(f):
        deadline = -1.0
        gr = None

        def bouncer(*a, **k):
            nonlocal deadline, gr
            t = deadline - time()
            while t > 0:
                gevent.sleep(t)
                t = deadline - time()
            gr = None
            deadline = time() + seconds
            f(*a, **k)

        @wraps(f)
        def wrapper(*a, **k):
            nonlocal deadline, gr
            t = deadline - time()
            if t < 0:
                f(*a, **k)
                deadline = time() + seconds
            else:
                gr = gr or gevent.spawn(bouncer, *a, **k)

        wrapper.__name__ == f.__name__
        return wrapper

    return decorate


class InstanceHookMeta(type):
    # ABCMeta would use __subclasshook__ for instance check. Loses information.

    def __instancecheck__(cls, inst):
        return cls.instancecheck(inst)

    def __subclasscheck__(cls, C):
        return cls.subclasscheck(C)

    def instancecheck(cls, inst):
        return cls.subclasscheck(type(inst))


class ArgValidationError(Exception):
    pass


class ArgTypeError(ArgValidationError):
    __slots__ = ('position', 'expected', 'actual')

    def __init__(self, position, expected, actual):
        self.position = position
        self.expected = expected
        self.actual = actual

    def __unicode__(self):
        return 'Arg %s should be "%s" type, "%s" found' % (
            self.position,
            self.expected.__name__,
            self.actual.__name__,
        )

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class ArgCountError(ArgValidationError):
    __slots__ = ('expected', 'actual')

    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual

    def __unicode__(self):
        return 'Expecting %s args, %s found' % (
            self.expected,
            self.actual,
        )

    def __str__(self):
        return self.__unicode__().encode('utf-8')


def validate_args(*typelist):
    def decorate(f):
        @wraps(f)
        def wrapper(*args):
            e, a = len(typelist), len(args)
            if e != a:
                raise ArgCountError(e, a)

            for i, e, v in zip(range(1000), typelist, args):
                if not isinstance(v, e):
                    raise ArgValidationError(i, e, v.__class__)

            return f(*args)

        wrapper.__name__ = f.__name__
        return wrapper

    return decorate


class BusinessException(Exception):
    snake_case: str


class BusinessExceptionGenerator(object):
    def __getattr__(self, k: str) -> Type[BusinessException]:
        snake_case = '_'.join([
            i.lower() for i in re.findall(r'[A-Z][a-z]+|[A-Z]+(?![a-z])', k)
        ])

        cls = type(k, (BusinessException,), {'snake_case': snake_case})
        setattr(self, k, cls)
        return cls


exceptions = BusinessExceptionGenerator()


# Helper to make mypy happy
class MockMeta(type):
    def mro(cls):
        bases = cls.__bases__
        assert len(bases) == 1
        return [cls, object]
