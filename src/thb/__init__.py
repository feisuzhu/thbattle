from __future__ import absolute_import

from thb.thb3v3 import THBattle
from thb.thbkof import THBattleKOF
from thb.thbidentity import THBattleIdentity
from thb.thbfaith import THBattleFaith
from thb.thb2v2 import THBattle2v2
from thb.thbnewbie import THBattleNewbie

import thb.item  # noqa, init it
from collections import OrderedDict

modes = OrderedDict()
l = [
    THBattle,
    THBattleKOF,
    THBattleIdentity,
    THBattleFaith,
    THBattle2v2,
    THBattleNewbie,
]

for g in l:
    modes[g.__name__] = g

del l, g, OrderedDict

modes_maoyu = {
    'THBattleNewbie',
    'THBattleKOF',
}
