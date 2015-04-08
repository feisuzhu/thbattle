# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
import time
import logging

# -- third party --
from pyglet.media import Player, SourceGroup
import pyglet

# -- own --
from .base.interp import InterpDesc, LinearInterp
from client.ui.resloader import L
from user_settings import UserSettings
from utils import instantiate

# -- code --
log = logging.getLogger('SoundManager')


class QueuedSoundPlayer(Player):
    def queue(self, source):
        source_group = SourceGroup(source.audio_format, source.video_format)
        source_group.queue(source)
        Player.queue(self, source_group)


class ManagedSoundPlayer(Player):
    def __init__(self, player_group):
        Player.__init__(self)
        player_group.append(self)
        self.player_group = player_group

    def delete(self):
        try:
            self.player_group.remove(self)
        except:
            log.exception('ManagedSoundPlayer have already been removed from player group')

        Player.delete(self)

    def on_source_group_eos(self):
        self.delete()


@instantiate
class SoundManager(object):
    volume_factor = InterpDesc('_volume_factor')  # 音量系数

    def __init__(self):
        self.cur_bgm = None
        self.bgm_next = None
        self.bgm_switching = False
        self.bgm_player = QueuedSoundPlayer()
        self.bgm_player.eos_action = Player.EOS_LOOP
        self.se_players = defaultdict(QueuedSoundPlayer)
        self.player_group = []
        self.muted = False
        self._se_suppress = time.time()

    def switch_bgm(self, bgm):
        if self.muted:
            self.bgm_next = bgm
            return

        if not self.cur_bgm:
            self.instant_switch_bgm(bgm)
            return

        if bgm == self.cur_bgm:
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
        self.bgm_player.queue(L(self.bgm_next))
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
        self._se_mute()
        pyglet.clock.unschedule(self._set_vol)
        pyglet.clock.unschedule(self._bgm_fade_out_done)
        self.bgm_next = self.cur_bgm
        self.cur_bgm = None

    def _se_mute(self):
        for player in self.player_group[:]:
            player.delete()

        for player in self.se_players.values():
            player.delete()

        self.se_players.clear()

    def unmute(self):
        if not self.muted: return
        self.muted = False
        self.bgm_next and self.instant_switch_bgm(self.bgm_next)

    def play(self, snd, queue=None):
        if self._se_suppress: return
        if self.muted: return

        if queue is None:
            player = ManagedSoundPlayer(self.player_group)
        else:
            player = self.se_players[queue]

        player.volume = self.se_volume
        player.queue(L(snd))
        player.play()

        return player

    def se_suppress(self):
        self._se_suppress = True

    def se_unsuppress(self):
        self._se_suppress = False

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
