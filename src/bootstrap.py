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
def bootstrap() -> Core:
    import logging

    from UnityEngine import Debug

    import utils.log
    import settings

    Debug.Log("bootstrap: Initializing logging")
    utils.log.init_unity(logging.ERROR, settings.SENTRY_DSN, settings.VERSION)
    utils.log.patch_gevent_hub_print_exception()

    Debug.Log("bootstrap: Before gevent")
    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_time()
    monkey.patch_select()
    Debug.Log("bootstrap: After gevent")

    from client.core import Core
    core = Core()
    return core
