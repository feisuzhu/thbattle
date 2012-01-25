import pyglet
import os

dn = os.path.dirname(__file__)
dn = os.path.join(dn, 'res')
ldr = pyglet.resource.Loader(dn)

card_shinesoft = ldr.image('shinesoft.tga')
card_hidden = ldr.image('card_hidden.tga')
char_portrait = ldr.image('char_portrait.tga')
del dn, ldr
