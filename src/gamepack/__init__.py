from thb import *
from collections import OrderedDict

gamemodes = OrderedDict()
l = [
    THBattle,
    THBattleKOF,
    THBattleIdentity5,
    THBattleIdentity,
    THBattleRaid,
]

for g in l:
    gamemodes[g.__name__] = g

del l, g, OrderedDict

def init_ui_resources():
    import gamepack.thb.ui
