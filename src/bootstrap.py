# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
from typing import TYPE_CHECKING

# -- own --
# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
def ignite(logfile: str) -> None:
    import logging
    import threading

    import utils.log
    import settings

    utils.log.init(logfile, logging.ERROR, settings.SENTRY_DSN, settings.VERSION)

    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_time()
    monkey.patch_select()

    from client.core import Core
    from core import CoreRunner
    core = Core()
    runner = CoreRunner(core)

    threading.Thread(target=runner.run, daemon=True).start()

