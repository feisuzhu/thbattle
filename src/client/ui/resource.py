import pyglet
from pyglet.resource import Loader, ResourceNotFoundException
import os
from utils import DataHolder
import itertools

texbin = pyglet.image.atlas.TextureBin(512, 512)
dummy_img = pyglet.image.ImageData(1, 1, 'RGBA', '\x00'*4)

class ResLoader(Loader):
    def __init__(self, path):
        global texbin
        self.texbin = texbin
        dn = os.path.dirname(path)
        dn = os.path.realpath(dn)
        dn = os.path.join(dn, 'res')
        pyglet.resource.Loader.__init__(self, dn)

    def file(self, name, mode='rb'):
        fn, ext = os.path.splitext(name)
        custom_name = fn + '_custom' + ext
        try:
            return Loader.file(self, custom_name, mode)
        except ResourceNotFoundException:
            pass

        return Loader.file(self, name, mode)

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
    worldmap = ldr.texture('worldmap.png')

    bg_gamelist = ldr.texture('bg_gamelist.png')
    bg_eventsbox = ldr.texture('bg_eventsbox.png')
    bg_chatbox = ldr.texture('bg_chatbox.png')

    card_shinesoft = tx('shinesoft.png')
    card_hidden = tx('card_hidden.png')
    card_question = tx('card_question.png')

    cardnumbers = pyglet.image.ImageGrid(img('cardnum.png'), 2, 13)
    cardnumbers = pyglet.image.TextureGrid(cardnumbers)

    suit = pyglet.image.ImageGrid(img('suit.png'), 1, 4)
    suit = pyglet.image.TextureGrid(suit)

    smallsuit = pyglet.image.ImageGrid(img('smallsuit.png'), 1, 4)
    smallsuit = pyglet.image.TextureGrid(smallsuit)


    num = pyglet.image.ImageGrid(img('num.png'), 1, 10)
    num = pyglet.image.TextureGrid(num)

    choosegirl_shine = tx('choosegirl_shine.png')

    actor_frame = anim('actor.png', [50] * 9, True)
    turn_frame = anim('turn.png', [50] * 9, True)

    ray = ldr.texture('ray.png')

    hurt = anim('hurt.png', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000])

    hp = ldr.texture('hp.png')
    hp_bg = ldr.texture('hp_bg.png')

    pbar = DataHolder()
    for fn in itertools.product(['b', 'bf', 's', 'sf'], ['l', 'm', 'r']):
        fn = ''.join(fn)
        setattr(pbar, fn, tx('pbar/%s.png' % fn))

    buttons = DataHolder()
    for t in ('blue', 'red', 'green', 'orange'):
        setattr(buttons, 'close_%s' % t, [
            tb.add(i) for i in
            pyglet.image.ImageGrid(img('buttons/closebtn_%s.png' % t), 1, 4)
        ])

    buttons.port_showncard = [
        tb.add(i) for i in
        pyglet.image.ImageGrid(img('buttons/port_showncard.png'), 1, 4)
    ]

    buttons.serverbtn = [
        tb.add(i) for i in
        pyglet.image.ImageGrid(img('buttons/serverbtn.png'), 1, 4)
    ]

    for k in args.keys(): del k
    del args
