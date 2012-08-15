from thb3v3 import THBattle, THBattle1v1DBG
from thbidentity import THBattleIdentity, THBattleIdentity5

from game.autoenv import Game

if Game.CLIENT_SIDE:
    import ui # force init
