# -*- coding: utf-8 -*-

# -- stdlib --
from cStringIO import StringIO
import hashlib
import os
import weakref

# -- third party --
from PIL import Image
from pyglet.resource import Loader
import pyglet

# -- own --
from utils import aes_decrypt, flatten


# -- code --
def get_atlas(atlas_name='__default__', atlas_size=(1024, 1024)):
    atlas = atlases.get(atlas_name)
    if not atlas:
        atlas = pyglet.image.atlas.TextureAtlas(*atlas_size)
        atlases[atlas_name] = atlas

    return atlas

atlases = {}
atlases['__default__'] = pyglet.image.atlas.TextureBin(512, 512)
define_atlas = get_atlas


class _ResourceDesc(object):
    __defaults__ = {}

    def __init__(self, *args):
        for k, v in self.__defaults__.items():
            setattr(self, k, v)

        for s, v in zip(self.__slots__, args):
            setattr(self, s, v)


class dummy(_ResourceDesc):
    __slots__ = ('name', )

    def __init__(self):
        self.name = '__dummy__'

    def load(self, loader):
        pass


class imgdata(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        fn = self.name + '.png'
        f = loader.file(fn)
        i = pyglet.image.load(fn, file=f)
        f.close()
        return i


class imgdata_grid(_ResourceDesc):
    __slots__ = ('name', 'rows', 'columns')

    def load(self, loader):
        img = imgdata(self.name).load(loader)
        img = pyglet.image.ImageGrid(img, self.rows, self.columns)
        return img


class img(_ResourceDesc):
    __slots__ = ('name', 'atlas')
    __defaults__ = {'atlas': '__default__'}

    def load(self, loader):
        i = imgdata(self.name).load(loader)
        atlas = get_atlas(self.atlas)
        return atlas.add(i)


class img_with_grayed(_ResourceDesc):
    __slots__ = ('name', 'atlas')
    __defaults__ = {'atlas': '__default__'}

    def load(self, loader):
        i = Image.open(loader.file(self.name + '.png'))
        w, h = i.size
        colored = i.convert('RGBA').tostring()
        grayed = i.convert('LA').convert('RGBA').tostring()
        colored = pyglet.image.ImageData(w, h, 'RGBA', colored, -w*4)
        grayed = pyglet.image.ImageData(w, h, 'RGBA', grayed, -w*4)
        atlas = get_atlas(self.atlas)
        tex = atlas.add(colored)
        tex.grayed = atlas.add(grayed)
        return tex


class img_grid(_ResourceDesc):
    __slots__ = ('name', 'rows', 'columns', 'atlas')
    __defaults__ = {'atlas': '__default__'}

    def load(self, loader):
        img = imgdata_grid(self.name, self.rows, self.columns).load(loader)
        atlas = get_atlas(self.atlas)
        img = [atlas.add(t) for t in img]
        return img


class anim(_ResourceDesc):
    __slots__ = ('name', 'durlist', 'loop', 'atlas')
    __defaults__ = {'atlas': '__default__', 'loop': False}
    dummy_img = pyglet.image.ImageData(1, 1, 'RGBA', '\x00'*4)

    def load(self, loader):
        img = imgdata(self.name).load(loader)
        durlist = self.durlist

        n = len(durlist)

        ig = pyglet.image.ImageGrid(img, 1, n)
        frames = []
        for i, (fi, dur) in enumerate(zip(ig, durlist)):
            f = pyglet.image.AnimationFrame(fi, dur/1000.0)
            frames.append(f)

        self.loop or frames.append(
            pyglet.image.AnimationFrame(self.dummy_img, None)
        )

        a = pyglet.image.Animation(frames)
        atlas = get_atlas(self.atlas)
        a.add_to_texture_bin(atlas)
        return a


class texture(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        return loader.texture(self.name + '.png')


class lazytexture(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        self.loader = loader
        self.reference = weakref.ref(lambda: 0)  # make a dead ref
        return self

    def get(self):
        obj = self.reference()
        if obj is not None:
            return obj

        obj = self.loader.texture(self.name + '.png')
        self.reference = weakref.ref(obj)
        return obj


class encrypted_texture(_ResourceDesc):
    __slots__ = ('name',)

    def load(self, loader):
        self.loader = loader
        self.reference = None
        self.decrypted = False
        hint = self.loader.file(self.name + '.hint').read()
        self.hint = hint
        return self

    def decrypt(self, passphrase):
        if self.reference:
            return False

        hint = self.hint.decode('base64')
        key = hashlib.sha256(passphrase).digest()
        hint2 = hashlib.sha256(key).digest()
        if hint != hint2:
            return False

        f = self.loader.file(self.name + '_encrypted.bin')
        dec = StringIO()
        data = aes_decrypt(f.read(), key)
        assert data.startswith('\x89PNG')
        dec.write(data)
        dec.seek(0)

        tex = pyglet.image.load('foo.png', file=dec)
        self.reference = tex
        self.decrypted = True
        return True

    def get(self):
        if not self.reference:
            raise Exception('Not decrypted!')

        return self.reference


class bgm(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        self.loader = loader
        return self

    def __call__(self):
        loader = self.loader
        return loader.media(loader.filename(self.name + '.ogg'))


class sound(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        snd = loader.media(
            loader.filename(self.name + '.ogg'), streaming=False
        )
        return snd


class subdir(_ResourceDesc):
    __slots__ = ('name', 'resdesc')

    def load(self, loader):
        res = _Resource(
            os.path.join(loader.path[0], self.name),
            self.resdesc,
        )
        res.load()
        return res


class _Resource(object):
    def __init__(self, path, resdesc):
        self.path = path
        self.resdesc = resdesc

    def load(self):
        loader = ResourceLoader(self.path)
        desclist = [
            i for i in flatten(self.resdesc)
            if isinstance(i, _ResourceDesc)
        ]

        for desc in desclist:
            res = desc.load(loader)
            setattr(self, desc.name, res)


class Resource(_Resource):
    loaded = False
    resources = []

    def __init__(self, *a):
        if self.__class__.loaded:
            raise Exception('Resource already loaded!')
        self.__class__.resources.append(self)
        _Resource.__init__(self, *a)

    @classmethod
    def load_resources(cls):
        cls.loaded = True
        for res in cls.resources:
            res.load()


class ResourceLoader(Loader):
    def filename(self, name):
        fn, ext = os.path.splitext(name)
        custom_name = fn + '_custom' + ext
        if os.path.exists(os.path.join(self.path[0], custom_name)):
            return custom_name
        else:
            return name

    def file(self, name, mode='rb'):
        return Loader.file(self, self.filename(name), mode)
