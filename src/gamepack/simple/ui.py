# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from utils.geometry import Rect

from game.autoenv import EventHandler, Action, GameError

class UIEventHook(EventHandler):
    def handle(self, evt, data):
        pass

class SimpleGameUI(Control):
    portrait_location = [ # [ ((x, y), (r, g, b)) ] * Game.n_persons
        ((352, 450), (0, 0, 0)),
        ((200, 150), (0, 0, 0)),
        ((500, 150), (0, 0, 0)),
    ]

    def __init__(self, game, *a, **k):
        self.game = game
        game.event_handlers.append(UIEventHook())
        Control.__init__(self, *a, **k)
