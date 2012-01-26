import pyglet
import os

dn = os.path.dirname(__file__)
dn = os.path.join(dn, 'res')
ldr = pyglet.resource.Loader(dn)

card_attack = ldr.image('attack.tga')
card_graze = ldr.image('graze.tga')
card_heal = ldr.image('heal.tga')

del dn, ldr
