# -*- coding: utf-8 -*-

import pyglet
from pyglet.media import Player
from .base.interp import InterpDesc, LinearInterp
from custom_options import options

cur_bgm = None
bgm_next = None
bgm_switching = False
bgm_player = Player()
bgm_player.eos_action = Player.EOS_LOOP

options.default('bgm_vol', 1.0)
options.default('mute', False)

if options.mute:
    vol = 0.0
else:
    vol = 1.0

def _set_vol(v = None):
    global vol
    if v:
        vol = v
    if options.mute:
        vol = 0.0
    bgm_player.volume = vol * options.bgm_vol

def _bgm_switcher(dt):
    global bgm_next, bgm_switching, vol, bgm_player, cur_bgm
    vol -= 0.1
    if vol <= 0.0:
        bgm_player.next()
        bgm_player.queue(bgm_next())
        _set_vol(1.0)
        bgm_player.play()
        bgm_switching = False
        cur_bgm = bgm_next
        bgm_next = None
        pyglet.clock.unschedule(_bgm_switcher)
    else:
        _set_vol()

def switch_bgm(bgm):
    global cur_bgm, bgm_next, bgm_switching

    if bgm is cur_bgm:
        return

    if not cur_bgm:
        instant_switch_bgm(bgm)

    else:
        bgm_next = bgm
        if not bgm_switching:
            bgm_switching = True
            pyglet.clock.schedule_interval(_bgm_switcher, 0.1)

def instant_switch_bgm(bgm):
    global vol, bgm_next
    pyglet.clock.unschedule(_bgm_switcher)
    bgm_next = bgm
    vol = 0.0
    _bgm_switcher(0)

def mute():
    options.mute = True
    _set_vol()

def unmute():
    options.mute = False
    _set_vol(1.0)

def set_volume(vol):
    options.bgm_vol = vol
    _set_vol(vol)

def play(snd):
    snd.play()
