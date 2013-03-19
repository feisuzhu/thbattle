# -*- coding: utf-8 -*-

import pyglet
from pyglet.media import Player, ManagedSoundPlayer
from .base.interp import InterpDesc, LinearInterp
from user_settings import UserSettings

from utils import instantiate


@instantiate
class SoundManager(object):
    volume_factor = InterpDesc('_volume_factor')  # 音量系数
    def __init__(self):
        us = UserSettings
        us.add_setting('bgm_muted', False)
        us.add_setting('se_muted', False)
        us.add_setting('bgm_vol', 1.0)
        us.add_setting('se_vol', 1.0)
        self.cur_bgm = None
        self.bgm_next = None
        self.bgm_switching = False
        self.bgm_player = Player()
        self.volume = us.bgm_vol  # 音量
        self.se_volume = us.se_vol
        self.bgm_player.eos_action = Player.EOS_LOOP
        self.muted = us.bgm_muted
        self.se_muted = us.se_muted

    def switch_bgm(self, bgm):
        if self.muted:
            self.bgm_next = bgm
            return

        if not self.cur_bgm:
            self.instant_switch_bgm(bgm)
            return

        if bgm is self.cur_bgm:
            return

        self.volume_factor = LinearInterp(1.0, 0.0, 1.0)

        self.bgm_next = bgm
        if not self.bgm_switching:
            self.bgm_switching = True
            pyglet.clock.schedule_interval(self._set_vol, 0.1)
            pyglet.clock.schedule_once(self._bgm_fade_out_done, 1.0)

    def _bgm_fade_out_done(self, _=None):
        pyglet.clock.unschedule(self._set_vol)
        self.bgm_player.next()
        self.bgm_player.queue(self.bgm_next())
        self.volume_factor = 1.0
        self._set_vol()
        self.bgm_player.play()
        self.bgm_switching = False
        self.cur_bgm = self.bgm_next
        self.bgm_next = None

    def instant_switch_bgm(self, bgm):
        pyglet.clock.unschedule(self._bgm_fade_out_done)
        self.bgm_next = bgm
        if not self.muted:
            self._bgm_fade_out_done()

    def mute(self, value = True, kind = 'bgm'):
        if kind == 'se':
            return self.mute_se() if value else self.unmute_se()

        if kind != 'bgm':
            return

        if value:
            if self.muted: return
            UserSettings.bgm_muted = True
            self.muted = True
            self.volume_factor = 0.0
            self.bgm_player.pause()
            pyglet.clock.unschedule(self._set_vol)
            pyglet.clock.unschedule(self._bgm_fade_out_done)
            self.bgm_next = self.cur_bgm
            self.cur_bgm = None
        else:
            self.unmute()

    def mute_se(self):
        UserSettings.se_muted = True
        self.se_muted = True

    def unmute(self):
        if not self.muted: return
        UserSettings.bgm_muted = False
        self.muted = False
        self.bgm_next and self.instant_switch_bgm(self.bgm_next)

    def unmute_se(self):
        UserSettings.se_muted = False
        self.se_muted = False

    def play(self, snd):
        if self.se_muted: return
        player = ManagedSoundPlayer()
        player.volume = self.se_volume
        player.queue(snd)
        player.play()

    def set_volume(self, vol, kind = 'bgm'):
        if kind == 'se':
            return self.set_se_volume(vol)

        if kind != 'bgm':
            return

        UserSettings.bgm_vol = vol
        self.volume = vol
        self._set_vol()

    def set_se_volume(self, vol):
        UserSettings.se_vol = vol
        self.se_volume = vol

    def _set_vol(self, _=None):
        self.bgm_player.volume = self.volume_factor * self.volume
