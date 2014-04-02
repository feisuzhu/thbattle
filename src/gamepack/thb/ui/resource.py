# -*- coding: utf-8 -*-

from client.ui.resloader import Resource, _ResourceDesc
from client.ui.resloader import anim, bgm, define_atlas, encrypted_texture
from client.ui.resloader import img, img_grid, img_with_grayed, lazytexture
from client.ui.resloader import sound, subdir, texture
import os

respath = os.path.join(os.path.dirname(__file__), 'res')
define_atlas('portrait', (1024, 2048))


class ui_meta(_ResourceDesc):
    __slots__ = ('name', )

    def load(self, loader):
        import gamepack.thb.ui.ui_meta  # noqa


resource = Resource(respath, [
    bgm('bgm_game'),

    [img_with_grayed('thblogo_' + i) for i in [
        '3v3', '8id', '5id', 'kof', 'raid', 'faith',
    ]],

    img('win'), img('lose'),
    anim('hurt', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000]),

    [img('card_' + i, 'card') for i in [
        'shinesoft', 'hidden', 'question', 'showncardtag',

        'attack', 'graze', 'heal', 'demolition', 'reject', 'sealarray',
        'nazrinrod', 'opticalcloak', 'greenufo', 'redufo', 'sinsack',
        'yukaridimension', 'duel', 'sinsackcarnival', 'mapcannon',
        'hakurouken', 'reactor', 'umbrella', 'roukanken', 'gungnir',
        'laevatein', 'repentancestick', 'wine', 'feast',
        'harvest', 'maidencostume', 'exinwan', 'ibukigourd', 'houraijewel',
        'saigyoubranch', 'ayaroundfan',
        'scarletrhapsodysword', 'deathsickle', 'keystone', 'witchbroom',
        'yinyangorb', 'suwakohat', 'phantom', 'icewing', 'grimoire',
        'dollcontrol', 'donationbox', 'frozenfrog', 'nenshaphone',
        'momijishield',

        'opticalcloak_small', 'greenufo_small', 'redufo_small',
        'hakurouken_small', 'reactor_small', 'umbrella_small',
        'roukanken_small', 'gungnir_small', 'laevatein_small',
        'repentancestick_small', 'maidencostume_small',
        'ibukigourd_small', 'houraijewel_small', 'saigyoubranch_small',
        'ayaroundfan_small', 'scarletrhapsodysword_small',
        'deathsickle_small', 'keystone_small', 'witchbroom_small',
        'yinyangorb_small', 'suwakohat_small', 'phantom_small',
        'icewing_small', 'grimoire_small', 'nenshaphone_small',
        'momijishield_small',
    ]],


    img('scardframe_normal', 'card'),
    img('scardframe_selected', 'card'),

    img_grid('cardnum', 2, 13, 'card'),
    img_grid('suit', 1, 4, 'card'),
    img_grid('smallsuit', 1, 4, 'card'),
    img_grid('smallnum', 2, 14, 'card'),

    anim('tag_sealarray', [83]*36, True),
    anim('tag_wine', [150]*3, True),
    anim('tag_lunaclock', [200]*10, True),
    img('tag_riverside'),
    img('tag_action'),
    img('tag_attacked'),
    img('tag_flandrecs'),
    img('tag_frozenfrog'),
    img('tag_gameintro'),
    img('tag_sinsack'),
    img('tag_ran_ei'),
    img_grid('tag_faiths', 1, 7),

    [img_with_grayed('%s_port' % p, 'portrait') for p in [
        'parsee', 'youmu', 'koakuma', 'marisa', 'daiyousei',
        'flandre', 'nazrin', 'alice', 'yugi', 'tewi',
        'patchouli', 'reimu', 'eirin', 'kogasa', 'shikieiki',
        'tenshi', 'rumia', 'yuuka', 'rinnosuke', 'ran',
        'remilia', 'minoriko', 'meirin', 'suika', 'chen',
        'yukari', 'cirno', 'sakuya', 'sanae', 'akari',
        'seiga', 'kaguya', 'momiji', 'komachi', 'mokou',
        'kokoro', 'mamizou', 'seija', 'kanako', 'medicine',

        'remilia_ex', 'remilia_ex2',
    ]],

    [lazytexture('%s_figure' % p) for p in [
        'daiyousei', 'eirin', 'koakuma', 'yukari', 'komachi',
        'kokoro', 'cirno', 'patchouli',
    ]],

    [encrypted_texture('%s_figure_alter' % p) for p in [
        'komachi', 'patchouli',
    ]],

    img_with_grayed('dummy_port', 'portrait'),

    img_with_grayed('hp', 'portrait'),
    img_with_grayed('hp_bg', 'portrait'),

    img_grid('num', 1, 10, 'portrait'),

    texture('remilia_ex_wallpaper'),

    bgm('bgm_remilia_ex'),

    subdir('sound', [
        sound('hit'),
    ]),

    ui_meta('thb_uimeta'),
])
