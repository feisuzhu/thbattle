from thb import *  # noqa
from collections import OrderedDict

gamemodes = OrderedDict()
l = [
    THBattle,
    THBattleKOF,
    THBattleIdentity5,
    THBattleIdentity,
    THBattleRaid,
    THBattleFaith,
    THBattle2v2,
]

for g in l:
    gamemodes[g.__name__] = g

del l, g, OrderedDict


def init_ui_resources():
    import gamepack.thb.ui.resource  # noqa
