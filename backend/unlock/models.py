# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from player.models import Player
from django.db import models

# -- own --


# -- code --
class Unlocked(models.Model):

    class Meta:
        verbose_name        = '解锁'
        verbose_name_plural = '解锁'
        unique_together = (
            ('player', 'item'),
        )

    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(
        Player, models.CASCADE, related_name='unlocks',
        verbose_name='玩家', help_text='玩家',
    )
    item = models.SlugField('解锁项目', max_length=256, help_text='解锁项目')  # character, skin, showgirl, achievement
    unlocked_at = models.DateTimeField('日期', auto_now_add=True, help_text='日期')

    def __str__(self):
        return f'{self.player.name} - {self.item}'


# RELATED FILES:
# schema.py
# admin.py
