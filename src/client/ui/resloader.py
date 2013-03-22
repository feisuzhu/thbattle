import pyglet
from pyglet.resource import Loader, ResourceNotFoundException
import os
from utils import DataHolder, flatten
import itertools
import Image

atlases = {}
atlases['__default__'] = pyglet.image.atlas.TextureBin(512, 512)


class _ResourceDesc(object):
    __defaults__ = {}
    def __init__(self, *args):
        d = dict(self.__defaults__)
        for k, v in self.__defaults__:
            setattr(self, k, v)

        for s, v in zip(self.__slots__, args):
            setattr(self, k, v)


class imgdata(_ResourceDesc):
    __slots__ = ('name', )
    def load(self, loader):
        f = loader.file(self.name + '.png')
        i = pyglet.image.load(fn, file=f)
        f.close()
        return i


class img(_ResourceDesc):
    __slots__ = ('name', 'atlas')
    __defaults__ = {'atlas': '__default__'}
    def load(self, loader):
        i = imgdata(self.name).load(loader)
        atlas = loader.get_atlas(self.atlas)
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
        atlas = loader.get_atlas(self.atlas)
        tex = atlas.add(colored)
        tex.grayed = atlas.add(grayed)
        return tex


class img_grid(_ResourceDesc):
    __slots__ = ('name', 'rows', 'columns', 'atlas')
    __defaults__ = {'atlas': '__default__'}
    def load(self, loader):
        img = imgdata(self.name).load(loader)
        img = pyglet.image.ImageGrid(img, self.rows, self.columns)
        atlas = loader.get_atlas(self.atlas)
        img = [atlas.add(t) for t in img]
        return img


class anim(_ResourceDesc):
    __slots__ = ('name', 'durlist', 'loop', 'atlas')
    __defaults__ = {'atlas': '__default__', 'loop': False}
    dummy_img = pyglet.image.ImageData(1, 1, 'RGBA', '\x00'*4)
    def load(self, loader):
        img = imgdata(self.name).load(loader)

        n = len(durlist)

        ig = pyglet.image.ImageGrid(img, 1, n)
        frames = []
        for i, (fi, dur) in enumerate(zip(ig, durlist)):
            f = pyglet.image.AnimationFrame(fi, dur/1000.0)
            frames.append(f)

        loop or frames.append(
            pyglet.image.AnimationFrame(self.dummy_img, None)
        )

        a = pyglet.image.Animation(frames)
        atlas = loader.get_atlas(self.atlas)
        a.add_to_texture_bin(atlas)
        return a


class texture(_ResourceDesc):
    __slots__ = ('name', )
    def load(self, loader):
        return loader.texture(
            loader.filename(self.name + '.png')
        )


class bgm(_ResourceDesc):
    __slots__ = ('name', )
    def load(self, loader):
        return lambda: loader.media(loader.filename(self.name + '.ogg'))


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

    @classmethod
    def load_resources(cls):
        cls.loaded = True
        for res in self.__class__.resources:
            res.load


class Resource(_Resource):
    loaded = False
    resources = []
    def __init__(self, *a):
        if self.__class__.loaded:
            raise Exception('Resource already loaded!')
        self.__class__.resources.append(self)
        _Resource.__init__(self, *a)


class ResourceLoader(Loader):
    def filename(self, name):
        fn, ext = os.path.splitext(name)
        custom_name = fn + '_custom' + ext
        if os.path.exists(os.path.join(self.respath, custom_name)):
            return custom_name
        else:
            return name

    def file(self, name, mode='rb'):
        return Loader.file(self, self.filename(name), mode)
    
    def get_atlas(self, atlas_name='__default__'):
        atlas = atlases.get(atlas_name)
        if not atlas:
            atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
            atlases[atlas_name] = atlas

        return atlas
