from thb import *  # noqa
from collections import OrderedDict

gamemodes = OrderedDict()
l = [
    THBattle,
    THBattleKOF,
    THBattleIdentity,
    THBattleFaith,
    THBattle2v2,
    THBattleBook,
    THBattleNewbie,
]

for g in l:
    gamemodes[g.__name__] = g

del l, g, OrderedDict

gamemodes_maoyu = {
    'THBattleNewbie',
    'THBattleKOF',
}


def init_ui_resources():
    import gamepack.thb.ui.resource  # noqa
