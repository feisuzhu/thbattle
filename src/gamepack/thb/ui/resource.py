import pyglet
import os

from client.ui.resource import ResLoader

with ResLoader(__file__) as args:
    locals().update(args)
    card_attack = tx('attack.tga')
    card_graze = tx('graze.tga')
    card_heal = tx('heal.tga')
    card_demolition = tx('card_demolition.tga')
    card_reject = tx('card_reject.tga')

    parsee_port = tx('parsee_port.png')
    youmu_port = tx('youmu_port.png')
    ldevil_port = tx('ldevil_port.png')

    for k in args.keys(): del k
    del args
