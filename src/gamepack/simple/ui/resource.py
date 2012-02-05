import pyglet
import os

from client.ui.resource import ResLoader

with ResLoader(__file__) as (_, img, anim):
    card_attack = img('attack.tga')
    card_graze = img('graze.tga')
    card_heal = img('heal.tga')
    del _, img, anim
