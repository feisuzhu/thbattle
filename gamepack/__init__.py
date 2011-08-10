from dummy import DummyGame
from simple import SimpleGame

gamemodes = { g.name:g for g in [
    DummyGame,
    SimpleGame,
]}
