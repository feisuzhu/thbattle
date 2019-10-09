# -*- coding: utf-8 -*-

# -- stdlib --
import re

# -- third party --
# -- own --
from client.ui.resloader import get_atlas, inventory

# -- code --
import thb.ui.ui_meta  # noqa

get_atlas('portrait', (1024, 2048))

inventory.extend([(re.compile('^%s$' % pat), ldr) for pat, ldr in (
    # ('thb-bgm_game',               ['bgm']),

    ('thb-modelogo-[a-z0-9_]+',    ['img']),

    ('thb-(win|lose)',             ['img']),

    ('thb-hurt',                   ['anim', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000]]),

    ('thb-card-[a-z0-9_]+',        ['img', 'card']),
    ('thb-card-small-[a-z0-9_]+',  ['img', 'card']),

    ('thb-cardnum',                ['img_grid', 2, 13, 'card']),  # FIXME: Screw this, meta should not be kept here
    ('thb-(small)?suit',           ['img_grid', 1, 4,  'card']),
    ('thb-smallnum',               ['img_grid', 2, 14, 'card']),

    ('thb-tag-sealarray',          ['anim', [83] * 36,  True]),
    ('thb-tag-wine',               ['anim', [150] * 3,  True]),
    ('thb-tag-lunadial',           ['anim', [200] * 10, True]),
    ('thb-tag-keine_devour',       ['anim', [150] * 13, True]),
    ('thb-tag-books',              ['img_grid', 1, 7]),
    ('thb-tag-[a-z_]+',            ['img']),

    ('thb-portrait-[a-z0-9_]+',    ['img_with_grayed', 'portrait']),

    ('thb-figure-[a-z_]+_alter',   ['encrypted_texture']),
    ('thb-figure-[a-z_]+',         ['lazytexture']),

    ('thb-hp(_bg)?',               ['img_with_grayed', 'portrait']),

    ('thb-num',                    ['img_grid', 1, 10, 'portrait']),

    ('thb-sound-[a-z0-9_]+',       ['sound']),

    ('thb-cv-[a-z0-9_-]+',         ['sound']),
)])
