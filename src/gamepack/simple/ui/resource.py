import pyglet
import os

from client.ui.resource import ResLoader

with ResLoader(__file__) as args:
    locals().update(args)
    card_attack = tx('attack.tga')
    card_graze = tx('graze.tga')
    card_heal = tx('heal.tga')
    for k in args.keys(): del locals()[k]
    del args
