# -*- coding: utf-8 -*-

# -- stdlib --
from cStringIO import StringIO
import hashlib
import os

# -- third party --
from PIL import Image
from pyglet.resource import Loader
import pyglet

# -- own --
from settings import BASEDIR
from utils import aes_decrypt

# -- code --
loader    = Loader(os.path.join(BASEDIR, 'resource'))
inventory = []
loaders   = {}
resources = {}

atlases = {}
atlases['__default__'] = pyglet.image.atlas.TextureBin(1024, 1024)


def get_atlas(atlas_name='__default__', atlas_size=(1024, 1024)):
    atlas = atlases.get(atlas_name)
    if not atlas:
        atlas = pyglet.image.atlas.TextureAtlas(*atlas_size)
        atlases[atlas_name] = atlas

    return atlas


def resloader(ext, no_cache=False, name=None):
    def decorate(f):
        loaders[name or f.__name__] = (f, ext, no_cache)
        return f

    return decorate


@resloader('')
def dummy(path):
    pass


@resloader('.png')
def imgdata(path):
    f = loader.file(path, 'rb')
    i = pyglet.image.load(path, file=f)
    f.close()
    return i


@resloader('.png')
def imgdata_grid(path, rows, columns):
    img = imgdata(path)
    img = pyglet.image.ImageGrid(img, rows, columns)
    return img


@resloader('.png')
def img(path, atlas='__default__'):
    i = imgdata(path)
    atlas = get_atlas(atlas)
    return atlas.add(i)


@resloader('.png')
def img_with_grayed(path, atlas='__default__'):
    i = Image.open(os.path.join(loader.location(path).path, path))
    w, h = i.size
    colored = i.convert('RGBA').tostring()
    grayed = i.convert('LA').convert('RGBA').tostring()
    colored = pyglet.image.ImageData(w, h, 'RGBA', colored, -w*4)
    grayed = pyglet.image.ImageData(w, h, 'RGBA', grayed, -w*4)
    atlas = get_atlas(atlas)
    tex = atlas.add(colored)
    tex.grayed = atlas.add(grayed)
    return tex


@resloader('.png')
def img_grid(path, rows, columns, atlas='__default__'):
    img = imgdata_grid(path, rows, columns)
    atlas = get_atlas(atlas)
    img = [atlas.add(t) for t in img]
    return img


@resloader('.png')
def anim(path, durlist, loop=False, atlas='__default__'):
    img = imgdata(path)

    n = len(durlist)

    ig = pyglet.image.ImageGrid(img, 1, n)
    frames = []
    for i, (fi, dur) in enumerate(zip(ig, durlist)):
        f = pyglet.image.AnimationFrame(fi, dur/1000.0)
        frames.append(f)

    loop or frames.append(
        pyglet.image.AnimationFrame(pyglet.image.ImageData(1, 1, 'RGBA', '\x00'*4), None)
    )

    a = pyglet.image.Animation(frames)
    atlas = get_atlas(atlas)
    a.add_to_texture_bin(atlas)
    return a


@resloader('.png')
@resloader('.png', True, 'lazytexture')
def texture(path):
    return loader.texture(path)


class EncryptedTexture(object):
    def __init__(self, path):
        self.path = path
        self.reference = None
        self.decrypted = False
        hint = loader.file(path + '.hint', 'rb').read()
        self.hint = hint

    def decrypt(self, passphrase):
        if self.reference:
            return False

        hint = self.hint.decode('base64')
        key = hashlib.sha256(passphrase).digest()
        hint2 = hashlib.sha256(key).digest()
        if hint != hint2:
            return False

        f = loader.file(self.path + '_encrypted.bin', 'rb')
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


@resloader('')
def encrypted_texture(path):
    return EncryptedTexture(path)


@resloader('.ogg', True)
def bgm(path):
    return loader.media(path)


@resloader('.ogg')
def sound(path):
    return loader.media(path, streaming=False)


def L(name):
    r = name.split('@')
    if len(r) > 1:
        import operator
        return reduce(operator.getitem, map(int, r[1:]), L(r[0]))

    res = resources.get(name)
    if res:
        return res

    for pattern, args in inventory:
        if pattern.match(name):
            break
    else:
        raise Exception('ResourceLoader: No rule applies for "%s"' % name)

    # args = ['loader_name', 'arg_1', 2]
    load, ext, no_cache = loaders[args[0]]

    path = name.replace('-', '/')

    if os.path.exists(os.path.join(BASEDIR, path + '_custom' + ext)):
        path = path + '_custom' + ext
    else:
        path = path + ext

    res = load(path, *args[1:])
    if not no_cache:
        resources[name] = res

    return res
