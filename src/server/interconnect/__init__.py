# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from options import options
from server.subsystem import Subsystem


# -- code --
if options.interconnect:
    from server.interconnect.redis import Interconnect
    Subsystem.interconnect = Interconnect.spawn(options.node, options.redis_url)
else:
    from server.interconnect.dummy import DummyInterconnect
    Subsystem.interconnect = DummyInterconnect()
