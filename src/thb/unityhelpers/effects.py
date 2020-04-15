# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --


# -- code --
def get_display_tags(p):
    from thb.meta.tags import get_display_tags as ui_tags
    return [i[0] for i in ui_tags(p)]
