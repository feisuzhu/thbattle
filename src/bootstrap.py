# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --

# -- third party --
# -- own --


# -- code --
def run_core() -> None:
    import logging

    import utils.log
    import settings

    utils.log.init_embedded(logging.INFO, settings.SENTRY_DSN, settings.VERSION)

    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_time()
    monkey.patch_select()

    from client.core import Core
    from core import CoreRunner
    core = Core()
    runner = CoreRunner(core)
    runner.run()
