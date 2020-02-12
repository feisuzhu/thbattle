# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, Dict
import logging

# -- third party --
from gevent.event import AsyncResult, Event
from gevent.greenlet import Greenlet
from gevent.pool import Pool

# -- own --

# -- code --
log = logging.getLogger('core')


class Core(object):
    core_type = ''
    _auto_id = 0

    runner: CoreRunner

    def __init__(self, **options: Dict[str, Any]):
        self._auto_id = Core._auto_id
        Core._auto_id += 1

        self._result = AsyncResult()
        self.tasks: Dict[str, Callable[[], None]] = {}
        self.options = options

    def __repr__(self) -> str:
        return f'Core[{self.core_type}{self._auto_id}]'

    @property
    def result(self):
        return self._result

    def crash(self, e):
        self._result.set_exception(e)

    def initialize(self, options: Dict[str, Any]) -> None:
        raise Exception('Abstract')


class CoreRunner(object):
    def __init__(self, core: Core):
        self.core = core
        self.pool = Pool()
        self.ready = Event()
        self.tasks: Dict[str, Greenlet] = {}

    def run(self) -> Any:
        core = self.core

        core.runner = self
        core.initialize(core.options)

        try:
            for k, f in core.tasks.items():
                log.debug('Spawning task [%s] for core %s', k, core)
                gr = self.pool.spawn(f)
                gr.gr_name = k
                self.tasks[k] = gr

            self.ready.set()
            return core.result.get()
        finally:
            self.shutdown()

    def spawn(self, fn, *args, **kw):
        return self.pool.spawn(fn, *args, **kw)

    def shutdown(self) -> None:
        self.pool.kill()
