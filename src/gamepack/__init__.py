from thb import *
from collections import OrderedDict

gamemodes = OrderedDict()
l = [
    THBattle,
    THBattleKOF,
    THBattle1v1DBG,
    THBattleIdentity5,
    THBattleIdentity,
]

for g in l:
    gamemodes[g.__name__] = g

del l, g, OrderedDict
