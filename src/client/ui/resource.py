import pyglet
import os
from utils import DataHolder
import itertools

texbin = pyglet.image.atlas.TextureBin(2048, 2048)
dummy_img = pyglet.image.ImageData(1, 1, 'RGBA', '\x00'*4)

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
        ldr = self

        def img(fn):
            f = self.file(fn)
            i = pyglet.image.load(fn, file=f)
            f.close()
            return i

        def tx(fn):
            return tb.add(img(fn))

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

        return locals()

    def __exit__(self, *exc_args):
        pass

with ResLoader(__file__) as args:
    locals().update(args)

    import zipfile
    fontzip = zipfile.ZipFile(ldr.file('font.zip'))
    font = {
        fn: fontzip.open(fn).read()
        for fn in fontzip.namelist()
    }
    fontzip.close()
    del zipfile, fontzip

    bg_login = ldr.texture('bg_login.png')
    bg_gamehall = ldr.texture('bg_gamehall.png')
    bg_ingame = ldr.texture('bg_ingame.png')

    bg_gamelist = tx('bg_gamelist.png')
    bg_eventsbox = tx('bg_eventsbox.png')
    bg_chatbox = tx('bg_chatbox.png')


    card_shinesoft = tx('shinesoft.tga')
    card_hidden = tx('card_hidden.tga')
    char_portrait = tx('char_portrait.tga')


    actor_frame = anim('actor.png', [50] * 9, True)
    turn_frame = anim('turn.png', [50] * 9, True)

    ray = tx('ray.tga')

    hurt = anim('hurt.png', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000])

    hp = ldr.texture('hp.tga')
    hp_bg = ldr.texture('hp_bg.tga')

    pbar = DataHolder()
    for fn in itertools.product(['b', 'bf', 's', 'sf'], ['l', 'm', 'r']):
        fn = ''.join(fn)
        setattr(pbar, fn, tx('pbar/%s.tga' % fn))

    border = [
        i.get_texture() for i in
        pyglet.image.ImageGrid(img('border.png'), 1, 9)
    ]

    buttons = DataHolder()
    for t in ('blue', 'red', 'green', 'orange'):
        setattr(buttons, 'close_%s' % t, [
            tb.add(i) for i in
            pyglet.image.ImageGrid(img('buttons/closebtn_%s.png' % t), 1, 4)
        ])

    for k in args.keys(): del k
    del args
