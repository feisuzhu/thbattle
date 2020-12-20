# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbunit
from thb.meta.common import ui_meta, UIMetaBare


# -- code --
@ui_meta(thbunit.THBattleCrash)
@ui_meta(thbunit.THBattleDummy1)
@ui_meta(thbunit.THBattleDummy2)
@ui_meta(thbunit.THBattleDummy3)
@ui_meta(thbunit.THBattleDummy4)
@ui_meta(thbunit.THBattleHalt)
@ui_meta(thbunit.THBattleHalt2)
class THBattleUnitMeta(UIMetaBare):
    name = '单元测试模式'
    logo = 'thb-modelogo-8id'
    description = 'description'

    params = {
        'double_curtain': [
            ('正常模式', False),
            ('双黑幕模式', True),
        ],
    }

    roles = {
        'HIDDEN':     {'name': '？',   'sprite': 'role-hidden'},
    }
