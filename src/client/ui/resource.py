# -*- coding: utf-8 -*-

# -- stdlib --
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


inventory.update({
    'c-bgm_hall':               ['bgm'],

    'c-bg_login':               ['lazytexture'],
    'c-bg_gamehall':            ['lazytexture'],
    'c-bg_ingame':              ['lazytexture'],
    'c-worldmap':               ['lazytexture'],
    'c-worldmap_shadow':        ['lazytexture'],
    'c-bg_gamelist':            ['lazytexture'],
    'c-bg_eventsbox':           ['lazytexture'],
    'c-bg_chatbox':             ['lazytexture'],

    'c-imagesel_shine':         ['img'],
    'c-imagesel_ban':           ['img'],
    'c-icon':                   ['imgdata'],

    'c-check':                  ['img'],

    'c-bgm_volume':             ['img'],
    'c-se_volume':              ['img'],
    'c-vol_icon':               ['img'],
    'c-vol_mute':               ['img'],

    'c-actor_frame':            ['anim', [50] * 9, True],
    'c-turn_frame':             ['anim', [50] * 9, True],

    'c-ray':                    ['texture'],

    'c-pbar-bl':                ['img'],
    'c-pbar-bm':                ['img'],
    'c-pbar-br':                ['img'],
    'c-pbar-bfl':               ['img'],
    'c-pbar-bfm':               ['img'],
    'c-pbar-bfr':               ['img'],
    'c-pbar-sl':                ['img'],
    'c-pbar-sm':                ['img'],
    'c-pbar-sr':                ['img'],
    'c-pbar-sfl':               ['img'],
    'c-pbar-sfm':               ['img'],
    'c-pbar-sfr':               ['img'],

    'c-buttons-close_blue':     ['img_grid', 1, 4],
    'c-buttons-close_red':      ['img_grid', 1, 4],
    'c-buttons-close_green':    ['img_grid', 1, 4],
    'c-buttons-close_orange':   ['img_grid', 1, 4],
    'c-buttons-port_showncard': ['img_grid', 1, 4],
    'c-buttons-replay':         ['img_grid', 1, 4],

    'c-sound-input':            ['sound'],

    'c-suit12':                 ['imgdata_grid', 1, 4],
    'c-suit16':                 ['imgdata_grid', 1, 4],

    'c-badges-dev':             ['img'],
    'c-badges-dsb_bronze':      ['img'],
    'c-badges-dsb_gold':        ['img'],
    'c-badges-dsb_silver':      ['img'],
    'c-badges-jcb_bronze':      ['img'],
    'c-badges-jcb_gold':        ['img'],
    'c-badges-jcb_silver':      ['img'],
    'c-badges-contributor':     ['img'],

    'c-white':                  ['white'],
    'c-font':                   ['font'],
})
