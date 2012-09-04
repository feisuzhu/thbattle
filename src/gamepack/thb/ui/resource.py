import pyglet
import os

from client.ui.resource import ResLoader

with ResLoader(__file__) as args:
    locals().update(args)

    bgm_game = lambda: ldr.media(ldr.filename('bgm_game.ogg'))

    thblogo_3v3 = tx('thblogo_3v3.png')
    thblogo_1v1dbg = tx('thblogo_1v1dbg.png')
    thblogo_8id = tx('thblogo_8id.png')
    thblogo_5id = tx('thblogo_5id.png')

    win = tx('win.png')
    lose = tx('lose.png')

    hurt = anim('hurt.png', [50, 50, 50, 50, 200, 30, 30, 30, 30, 2000])

    card_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)

    def card_tx(fn):
        return card_atlas.add(img(fn))

    card_shinesoft = card_tx('shinesoft.png')
    card_hidden = card_tx('card_hidden.png')
    card_question = card_tx('card_question.png')

    card_attack = card_tx('card_attack.png')
    tag_attacked = anim('tag_attacked.png', [10000], True)
    card_graze = card_tx('card_graze.png')
    card_heal = card_tx('card_heal.png')
    card_demolition = card_tx('card_demolition.png')
    card_reject = card_tx('card_reject.png')
    card_sealarray = card_tx('card_sealarray.png')
    tag_sealarray = anim('tag_sealarray.png', [83]*36, True)

    card_nazrinrod= card_tx('card_nazrinrod.png')
    card_opticalcloak = card_tx('card_opticalcloak.png')
    card_greenufo = card_tx('card_greenufo.png')
    card_redufo = card_tx('card_redufo.png')
    card_sinsack = card_tx('card_sinsack.png')
    tag_sinsack = anim('tag_sinsack.png', [10000], True)
    card_yukaridimension = card_tx('card_yukaridimension.png')
    card_duel = card_tx('card_duel.png')
    card_sinsackcarnival = card_tx('card_sinsackcarnival.png')
    card_mapcannon = card_tx('card_mapcannon.png')
    card_hakurouken = card_tx('card_hakurouken.png')
    card_reactor = card_tx('card_reactor.png')
    card_umbrella = card_tx('card_umbrella.png')
    card_roukanken = card_tx('card_roukanken.png')
    card_gungnir = card_tx('card_gungnir.png')
    card_laevatein = card_tx('card_laevatein.png')
    card_trident = card_tx('card_trident.png')
    card_repentancestick = card_tx('card_repentancestick.png')
    card_wine = card_tx('card_wine.png')
    tag_wine = anim('tag_wine.png', [150]*3, True)
    card_feast = card_tx('card_feast.png')
    card_harvest = card_tx('card_harvest.png')
    card_maidencostume = card_tx('card_maidencostume.png')
    card_exinwan = card_tx('card_exinwan.png')
    card_ibukigourd = card_tx('card_ibukigourd.png')
    card_houraijewel = card_tx('card_houraijewel.png')
    card_saigyoubranch = card_tx('card_saigyoubranch.png')
    card_flirtingsword = card_tx('card_flirtingsword.png')
    card_camera = card_tx('card_camera.png')
    card_ayaroundfan = card_tx('card_ayaroundfan.png')
    card_scarletrhapsodysword = card_tx('card_scarletrhapsodysword.png')
    card_deathsickle = card_tx('card_deathsickle.png')
    card_keystone = card_tx('card_keystone.png')
    card_witchbroom = card_tx('card_witchbroom.png')
    card_yinyangorb = card_tx('card_yinyangorb.png')
    card_suwakohat = card_tx('card_suwakohat.png')
    card_phantom = card_tx('card_phantom.png')
    card_icewing = card_tx('card_icewing.png')
    card_grimoire = card_tx('card_grimoire.png')
    card_dollcontrol = card_tx('card_dollcontrol.png')
    card_donationbox = card_tx('card_donationbox.png')

    card_opticalcloak_small = card_tx('card_opticalcloak_small.png')
    card_greenufo_small = card_tx('card_greenufo_small.png')
    card_redufo_small = card_tx('card_redufo_small.png')
    card_hakurouken_small = card_tx('card_hakurouken_small.png')
    card_reactor_small = card_tx('card_reactor_small.png')
    card_umbrella_small = card_tx('card_umbrella_small.png')
    card_roukanken_small = card_tx('card_roukanken_small.png')
    card_gungnir_small = card_tx('card_gungnir_small.png')
    card_laevatein_small = card_tx('card_laevatein_small.png')
    card_trident_small = card_tx('card_trident_small.png')
    card_repentancestick_small = card_tx('card_repentancestick_small.png')
    card_maidencostume_small = card_tx('card_maidencostume_small.png')
    card_ibukigourd_small = card_tx('card_ibukigourd_small.png')
    card_houraijewel_small = card_tx('card_houraijewel_small.png')
    card_saigyoubranch_small = card_tx('card_saigyoubranch_small.png')
    card_flirtingsword_small = card_tx('card_flirtingsword_small.png')
    card_ayaroundfan_small = card_tx('card_ayaroundfan_small.png')
    card_scarletrhapsodysword_small = card_tx('card_scarletrhapsodysword_small.png')
    card_deathsickle_small = card_tx('card_deathsickle_small.png')
    card_keystone_small = card_tx('card_keystone_small.png')
    card_witchbroom_small = card_tx('card_witchbroom_small.png')
    card_yinyangorb_small = card_tx('card_yinyangorb_small.png')
    card_suwakohat_small = card_tx('card_suwakohat_small.png')
    card_phantom_small = card_tx('card_phantom_small.png')
    card_icewing_small = card_tx('card_icewing_small.png')
    card_grimoire_small = card_tx('card_grimoire_small.png')

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

    parsee_port = tx('parsee_port.png')
    youmu_port = tx('youmu_port.png')
    koakuma_port = tx('koakuma_port.png')
    marisa_port = tx('marisa_port.png')
    daiyousei_port = tx('daiyousei_port.png')
    flandre_port = tx('flandre_port.png')
    tag_flandrecs = anim('tag_flandrecs.png', [10000], True)
    nazrin_port = tx('nazrin_port.png')
    alice_port = tx('alice_port.png')
    yugi_port = tx('yugi_port.png')
    tewi_port = tx('tewi_port.png')
    patchouli_port = tx('patchouli_port.png')
    reimu_port = tx('reimu_port.png')
    eirin_port = tx('eirin_port.png')
    kogasa_port = tx('kogasa_port.png')
    shikieiki_port = tx('shikieiki_port.png')
    tenshi_port = tx('tenshi_port.png')
    rumia_port = tx('rumia_port.png')
    yuuka_port = tx('yuuka_port.png')
    rinnosuke_port = tx('rinnosuke_port.png')
    ran_port = tx('ran_port.png')
    remilia_port = tx('remilia_port.png')
    minoriko_port = tx('minoriko_port.png')
    meirin_port = tx('meirin_port.png')
    suika_port = tx('suika_port.png')
    chen_port = tx('chen_port.png')

    for k in args.keys(): del k
    del args
