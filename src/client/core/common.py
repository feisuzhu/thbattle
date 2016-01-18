# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import gevent

# -- own --


# -- code --
class ForcedKill(gevent.GreenletExit):
    pass
