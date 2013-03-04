import pyglet
import os

from client.ui.resource import ResLoader

ldr = ResLoader(__file__)
with ldr as args:
    locals().update(args)

    bgm_game = lambda: ldr.media(ldr.filename('bgm_game.ogg'))

    thblogo_3v3 = tx_with_grayed('thblogo_3v3.png')
    thblogo_8id = tx_with_grayed('thblogo_8id.png')
    thblogo_5id = tx_with_grayed('thblogo_5id.png')
    thblogo_kof = tx_with_grayed('thblogo_kof.png')
    thblogo_raid = tx_with_grayed('thblogo_raid.png')

    win = tx('win.png')
    lose = tx('lose.png')

    hurt = anim('hurt.png', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000])

    card_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)

    def card_tx(fn):
        return card_atlas.add(img(fn))

    cards = (
        'shinesoft', 'hidden', 'question', 'showncardtag',

        'attack', 'graze', 'heal', 'demolition', 'reject', 'sealarray',
        'nazrinrod', 'opticalcloak', 'greenufo', 'redufo', 'sinsack',
        'yukaridimension', 'duel', 'sinsackcarnival', 'mapcannon',
        'hakurouken', 'reactor', 'umbrella', 'roukanken', 'gungnir',
        'laevatein', 'trident', 'repentancestick', 'wine', 'feast',
        'harvest', 'maidencostume', 'exinwan', 'ibukigourd', 'houraijewel',
        'saigyoubranch', 'flirtingsword', 'camera', 'ayaroundfan',
        'scarletrhapsodysword', 'deathsickle', 'keystone', 'witchbroom',
        'yinyangorb', 'suwakohat', 'phantom', 'icewing', 'grimoire',
        'dollcontrol', 'donationbox', 'frozenfrog', 'lottery',
        
        'opticalcloak_small', 'greenufo_small', 'redufo_small',
        'hakurouken_small', 'reactor_small', 'umbrella_small',
        'roukanken_small', 'gungnir_small', 'laevatein_small',
        'trident_small', 'repentancestick_small', 'maidencostume_small',
        'ibukigourd_small', 'houraijewel_small', 'saigyoubranch_small',
        'flirtingsword_small', 'ayaroundfan_small', 'scarletrhapsodysword_small',
        'deathsickle_small', 'keystone_small', 'witchbroom_small',
        'yinyangorb_small', 'suwakohat_small', 'phantom_small',
        'icewing_small', 'grimoire_small',
    )

    for cn in cards:
        tex = card_tx('card_%s.png' % cn)
        exec 'card_%s = tex' % cn in locals()

    scardframe_normal = card_tx('scardframe_normal.png')
    scardframe_selected = card_tx('scardframe_selected.png')

    cardnumbers = pyglet.image.ImageGrid(img('cardnum.png'), 2, 13)
    cardnumbers = [card_atlas.add(t) for t in cardnumbers]

    suit = pyglet.image.ImageGrid(img('suit.png'), 1, 4)
    suit = [card_atlas.add(t) for t in suit]

    smallsuit = pyglet.image.ImageGrid(img('smallsuit.png'), 1, 4)
    smallsuit = [card_atlas.add(t) for t in smallsuit]

    smallnum = pyglet.image.ImageGrid(img('cardnum_small.png'), 2, 14)
    smallnum = [card_atlas.add(t) for t in smallnum]

    del card_tx

    tag_flandrecs = anim('tag_flandrecs.png', [10000], True)
    tag_attacked = anim('tag_attacked.png', [10000], True)
    tag_sealarray = anim('tag_sealarray.png', [83]*36, True)
    tag_sinsack = anim('tag_sinsack.png', [10000], True)
    tag_wine = anim('tag_wine.png', [150]*3, True)
    tag_frozenfrog = anim('tag_frozenfrog.png', [10000], True)
    tag_lunaclock = anim('tag_lunaclock.png', [200]*10, True)

    port_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)

    ports = ['%s_port' % p  for p in [
        'parsee', 'youmu', 'koakuma', 'marisa', 'daiyousei',
        'flandre', 'nazrin', 'alice', 'yugi', 'tewi',
        'patchouli', 'reimu', 'eirin', 'kogasa', 'shikieiki',
        'tenshi', 'rumia', 'yuuka', 'rinnosuke', 'ran',
        'remilia', 'minoriko', 'meirin', 'suika', 'chen',
        'yukari', 'cirno', 'sakuya', 'sanae', 'akari',
        'seiga',

        'remilia_ex', 'remilia_ex2',
    ]]

    from options import options
    if options.testing:
        ports.append('dummy_port')

    del options

    ports.extend([
        'hp', 'hp_bg',
    ])

    for p in ports:
        tex = tx_with_grayed('%s.png' % p, port_atlas)
        exec '%s = tex' % p in locals()

    num = pyglet.image.ImageGrid(img('num.png'), 1, 10)
    num = [port_atlas.add(t) for t in num]

    remilia_ex_wallpaper = ldr.texture(ldr.filename('remilia_ex_wallpaper.png'))
    bgm_remilia_ex = lambda: ldr.media(ldr.filename('bgm_remilia_ex.ogg'))

    class sound:
        hit = ldr.media(ldr.filename('se/hit.ogg'), streaming=False)

    for k in args.keys(): del k
    del args
