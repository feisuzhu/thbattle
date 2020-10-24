# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING
import os
import os.path
import sys

# -- third party --
# -- own --
# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
def unhandled_exception(etype, value, tb):
    try:
        import traceback
        fn = os.path.join(workdir, 'exception.log')
        with open(fn, 'w') as f:
            f.write(traceback.format_exception(etype, value, tb))
    except:  # noqa
        pass


def run_core() -> None:
    import logging
    import threading

    import utils.log
    import settings

    workdir = os.environ['APPLICATION_WORKING_DIR']

    utils.log.init_embedded(os.path.join(workdir, 'client.log'), logging.INFO, settings.SENTRY_DSN, settings.VERSION)

    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_time()
    monkey.patch_select()

    from client.core import Core
    from core import CoreRunner
    core = Core()
    runner = CoreRunner(core)
    runner.run()
