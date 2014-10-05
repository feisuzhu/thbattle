# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
import time

# -- third party --
from pyglet.media import ManagedSoundPlayer, Player
import pyglet

# -- own --
from .base.interp import InterpDesc, LinearInterp
from user_settings import UserSettings
from utils import instantiate


# -- code --
@instantiate
class SoundManager(object):
    volume_factor = InterpDesc('_volume_factor')  # 音量系数

    def __init__(self):
        self.cur_bgm = None
        self.bgm_next = None
        self.bgm_switching = False
        self.bgm_player = Player()
        self.bgm_player.eos_action = Player.EOS_LOOP
        self.se_players = defaultdict(Player)
        self.muted = False
        self._se_suppress = time.time()

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

    def mute(self):
        if self.muted: return
        self.muted = True
        self.volume_factor = 0.0
        self.bgm_player.pause()
        pyglet.clock.unschedule(self._set_vol)
        pyglet.clock.unschedule(self._bgm_fade_out_done)
        self.bgm_next = self.cur_bgm
        self.cur_bgm = None

    def unmute(self):
        if not self.muted: return
        self.muted = False
        self.bgm_next and self.instant_switch_bgm(self.bgm_next)

    def play(self, snd, queue=None):
        t = time.time()
        if t - self._se_suppress < 3:
            self._se_suppress = t
            return

        if self.muted: return

        if queue is None:
            player = ManagedSoundPlayer()
        else:
            player = self.se_players[queue]

        player.volume = self.se_volume
        player.queue(snd)
        player.play()

    def se_suppress(self):
        self._se_suppress = time.time()

    @property
    def bgm_volume(self):
        return UserSettings.bgm_volume

    @bgm_volume.setter
    def bgm_volume(self, value):
        UserSettings.bgm_volume = value
        self._set_vol()

    @property
    def se_volume(self):
        return UserSettings.se_volume

    @se_volume.setter
    def se_volume(self, value):
        UserSettings.se_volume = value
        self._set_vol()

    def _set_vol(self, _=None):
        self.bgm_player.volume = self.volume_factor * self.bgm_volume
        for p in self.se_players.values():
            p.volume = self.volume_factor * self.se_volume
