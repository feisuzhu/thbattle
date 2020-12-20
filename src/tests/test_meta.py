# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging

# -- third party --

# -- own --


# -- code --
log = logging.getLogger('UnitTest')


class TestMeta(object):
    def testViewCharacter(self):
        from thb.characters.base import Character
        from thb.meta import characters  # noqa
        from game.base import Player
        from thb.meta import view

        p = Player()
        p.pid = 1

        for cls in Character.classes.values():
            view.character_cls(cls)
            view.character(cls(p))
