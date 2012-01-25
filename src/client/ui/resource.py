import pyglet
import os

dn = os.path.dirname(__file__)
dn = os.path.join(dn, 'res')
ldr = pyglet.resource.Loader(dn)

card_shinesoft = ldr.image('shinesoft.tga')

del dn, ldr
