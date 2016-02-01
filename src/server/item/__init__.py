# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from server.subsystem import Subsystem
from server.item.subsystem import ItemSystem


# -- code --
Subsystem.item = ItemSystem()
