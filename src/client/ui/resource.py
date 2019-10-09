# -*- coding: utf-8 -*-

# -- stdlib --
import re
import zipfile

# -- third party --
import pyglet

# -- own --
from client.ui.resloader import resloader, loader, inventory, get_atlas


# -- code --
@resloader('.zip')
def font(path):
    fontzip = zipfile.ZipFile(loader.file(path, 'rb'))
    font = {
        fn: fontzip.open(fn).read()
        for fn in fontzip.namelist()
    }
    fontzip.close()
    return font


@resloader('')
def white(path):
    atlas = get_atlas()
    white = atlas.add(pyglet.image.ImageData(4, 4, 'RGBA', '\xFF'*64))
    c = white.tex_coords
    f = c[0:3]; t = c[6:9]
    white.tex_coords = ((f[0] + t[0]) / 2, (f[1] + t[1]) / 2, 0) * 4
    return white


inventory.extend([(re.compile('^%s$' % pat), ldr) for pat, ldr in (
    # (r'c-bgm_hall',            ['bgm']),

    (r'c-bg_[a-z_]+',          ['lazytexture']),

    (r'c-imagesel_.*',         ['img']),
    (r'c-icon',                ['imgdata']),

    (r'c-check',               ['img']),

    (r'c-(bgm|se)_volume',     ['img']),
    (r'c-vol_(icon|mute)',     ['img']),

    (r'c-(actor|turn)_frame',  ['anim', [50] * 9, True]),

    (r'c-ray',                 ['texture']),
    (r'c-pbar-[a-z]+',         ['img']),
    (r'c-buttons-[a-z_]+',     ['img_grid', 1, 4]),
    (r'c-sound-input',         ['sound']),
    (r'c-suit1[26]',           ['imgdata_grid', 1, 4]),
    (r'c-white',               ['white']),
    (r'c-font',                ['font']),
)])
