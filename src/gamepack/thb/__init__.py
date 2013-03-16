from thb3v3 import THBattle
from thbkof import THBattleKOF
from thbraid import THBattleRaid
from thbidentity import THBattleIdentity, THBattleIdentity5

from game.autoenv import Game

if Game.CLIENT_SIDE and Game.CLIENT_SIDE != 'blah':  # HACK for replay.py
    import ui  # force init
