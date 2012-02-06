import pyglet
import os
from utils import DataHolder
import itertools

texbin = pyglet.image.atlas.TextureBin(2048, 2048)
dummy_img = pyglet.image.ImageData(1, 1, '\x00' * 4, 'RGBA')

class ResLoader(pyglet.resource.Loader):
    def __init__(self, path):
        global texbin
        self.texbin = texbin
        dn = os.path.dirname(path)
        dn = os.path.realpath(dn)
        dn = os.path.join(dn, 'res')
        pyglet.resource.Loader.__init__(self, dn)

    def __enter__(self):
        tb = self.texbin
        def img(fn):
            f = self.file(fn)
            i = pyglet.image.load(fn, file=f)
            f.close()
            return tb.add(i)

        def anim(fn, durlist, loop=False):
            f = self.file(fn)
            img = pyglet.image.load(fn, file=f)
            f.close()

            n = len(durlist)

            ig = pyglet.image.ImageGrid(img, 1, n)
            frames = []
            for i, (fi, dur) in enumerate(zip(ig, durlist)):
                f = pyglet.image.AnimationFrame(fi, dur/1000.0)
                frames.append(f)
            if not loop:
                frames.append(
                    pyglet.image.AnimationFrame(dummy_img, None)
                )
            a = pyglet.image.Animation(frames)
            a.add_to_texture_bin(tb)
            return a

        return self, img, anim

    def __exit__(self, *exc_args):
        pass

with ResLoader(__file__) as (ldr, img, anim):
    card_shinesoft = img('shinesoft.tga')
    card_hidden = img('card_hidden.tga')
    char_portrait = img('char_portrait.tga')
    ray = img('ray.tga')

    actor_frame = anim('actor.png', [50] * 9, True)
    turn_frame = anim('turn.png', [50] * 9, True)

    hurt = anim('hurt.png', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000])

    hp = ldr.texture('hp.tga')
    hp_bg = ldr.texture('hp_bg.tga')

    pbar = DataHolder()
    for fn in itertools.product(['b', 'bf', 's', 'sf'], ['l', 'm', 'r']):
        fn = ''.join(fn)
        setattr(pbar, fn, img(os.path.join('pbar', fn + '.tga')))
        
    del ldr, img, anim
