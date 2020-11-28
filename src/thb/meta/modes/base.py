# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import mode
from thb.meta.common import ui_meta, UIMetaBare
from thb.meta.translator import handle_event


# -- code --
@ui_meta(mode.THBattle)
class THBattle(UIMetaBare):
    name: str
    logo: str
    description: str
    params_disp: dict
    roles_disp: dict
    event_translator = staticmethod(handle_event)
