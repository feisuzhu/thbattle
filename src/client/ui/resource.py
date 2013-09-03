import pyglet
from pyglet.resource import Loader
import zipfile

from client.ui.resloader import anim, bgm, get_atlas, img, imgdata_grid, img_grid, Resource, sound, subdir, texture, imgdata
from client.ui.resloader import _ResourceDesc
import os

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

    texture('bg_login'),
    texture('bg_gamehall'),
    texture('bg_ingame'),
    texture('worldmap'),
    texture('bg_gamelist'),
    texture('bg_eventsbox'),
    texture('bg_chatbox'),

    img('imagesel_shine'),
    imgdata('icon'),

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
        img_grid('serverbtn', 1, 4),
    ]),


    subdir('sound', [
        sound('input'),
    ]),

    imgdata_grid('suit12', 1, 4), imgdata_grid('suit16', 1, 4),

    white('white'),
])
