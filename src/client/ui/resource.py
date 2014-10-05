# -*- coding: utf-8 -*-

# -- stdlib --
import os
import zipfile

# -- third party --
from pyglet.resource import Loader
import pyglet

# -- own --
from client.ui.resloader import Resource, _ResourceDesc, anim, bgm, get_atlas, img, img_grid
from client.ui.resloader import imgdata, imgdata_grid, lazytexture, sound, subdir, texture

# -- code --

respath = os.path.join(os.path.dirname(__file__), 'res')

# special case for font
ldr = Loader(respath)
fontzip = zipfile.ZipFile(ldr.file('font.zip'))
font = {
    fn: fontzip.open(fn).read()
    for fn in fontzip.namelist()
}
fontzip.close()
del fontzip, ldr


class white(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        atlas = get_atlas()
        white = atlas.add(pyglet.image.ImageData(4, 4, 'RGBA', '\xFF'*64))
        c = white.tex_coords
        f = c[0:3]; t = c[6:9]
        white.tex_coords = ((f[0] + t[0]) / 2, (f[1] + t[1]) / 2, 0) * 4
        return white


resource = Resource(respath, [
    bgm('bgm_hall'),

    lazytexture('bg_login'),
    lazytexture('bg_gamehall'),
    lazytexture('bg_ingame'),
    lazytexture('worldmap'),
    lazytexture('worldmap_shadow'),
    lazytexture('bg_gamelist'),
    lazytexture('bg_eventsbox'),
    lazytexture('bg_chatbox'),

    img('imagesel_shine'),
    img('imagesel_ban'),
    imgdata('icon'),

    img('check'),

    img('bgm_volume'),
    img('se_volume'),
    img('vol_icon'),
    img('vol_mute'),

    anim('actor_frame', [50] * 9, True),
    anim('turn_frame', [50] * 9, True),

    texture('ray'),

    subdir('pbar', [img(i) for i in [
        'bl', 'bm', 'br',
        'bfl', 'bfm', 'bfr',
        'sl', 'sm', 'sr',
        'sfl', 'sfm', 'sfr',
    ]]),

    subdir('buttons', [
        [
            img_grid('close_' + t, 1, 4)
            for t in ('blue', 'red', 'green', 'orange')
        ],
        img_grid('port_showncard', 1, 4),
        img_grid('replay', 1, 4),
    ]),

    subdir('sound', [
        sound('input'),
    ]),

    imgdata_grid('suit12', 1, 4), imgdata_grid('suit16', 1, 4),

    subdir('badges', [img(i) for i in [
        'dev',
        'dsb_bronze',
        'dsb_gold',
        'dsb_silver',
        'jcb_bronze',
        'jcb_gold',
        'jcb_silver',
        'contributor',
    ]]),

    white('white'),
])
