# -*- coding: utf-8 -*-

import pyglet
from pyglet.media import Player
from .base.interp import InterpDesc, LinearInterp

cur_bgm = None
bgm_next = None
bgm_switching = False
bgm_player = Player()
bgm_player.eos_action = Player.EOS_LOOP
_mute = False

vol = 1.0

def _bgm_switcher(dt):
    global bgm_next, bgm_switching, vol, bgm_player, cur_bgm, _mute
    vol -= 0.1
    if vol <= 0.0:
        bgm_player.pause()
        bgm_player.queue(bgm_next())
        if _mute:
            vol = 0.0
        else:
            vol = 1.0
        bgm_player.volume = vol
        bgm_player.next()
        bgm_player.play()
        bgm_switching = False
        cur_bgm = bgm_next
        bgm_next = None
        pyglet.clock.unschedule(_bgm_switcher)
    else:
        bgm_player.volume = vol

def switch_bgm(bgm):
    global cur_bgm, bgm_next, bgm_switching, _mute
    if _mute: return

    if bgm is cur_bgm:
        return
    if not cur_bgm:
        bgm_player.queue(bgm())
        bgm_player.play()
        cur_bgm = bgm
    else:
        bgm_next = bgm
        if not bgm_switching:
            bgm_switching = True
            pyglet.clock.schedule_interval(_bgm_switcher, 0.1)

def mute():
    global _mute
    _mute = True
    bgm_player.volume = 0.0

def play(snd):
    snd.play()
