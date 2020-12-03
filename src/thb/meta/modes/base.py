# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Dict, List, Tuple, TypedDict

# -- third party --
# -- own --
from thb import mode
from thb.meta.common import UIMetaBare, ui_meta
from thb.meta.translator import handle_event


# -- code --
class RoleDisp(TypedDict):
    name: str
    sprite: str


@ui_meta(mode.THBattle)
class THBattle(UIMetaBare):
    name: str
    logo: str
    description: str
    params: Dict[str, List[Tuple[str, Any]]]
    roles: Dict[str, RoleDisp]
    event_translator = staticmethod(handle_event)
