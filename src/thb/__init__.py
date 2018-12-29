# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Dict, Type

# -- third party --
# -- own --
from thb.mode import THBattle
from thb.thb2v2 import THBattle2v2
from thb.thbfaith import THBattleFaith
from thb.thbrole import THBattleRole
from thb.thbkof import THBattleKOF
from thb.thbnewbie import THBattleNewbie


# -- code --
import thb.item  # noqa, init it
import thb.meta  # noqa, init it

modes: Dict[str, Type[THBattle]] = {}
modelst = [
    THBattleKOF,
    THBattleRole,
    THBattleFaith,
    THBattle2v2,
    THBattleNewbie,
]

for g in modelst:
    modes[g.__name__] = g

del modelst, g

modes_kedama = {
    'THBattleNewbie',
    'THBattleKOF',
}
