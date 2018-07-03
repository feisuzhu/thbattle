# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Unlocked)
class UnlockedAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'item')
    list_filter = ()
    search_fields = ('player__name', 'item')
    ordering = ('player',)


@admin.register(models.Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'achievement')
    list_filter = ()
    search_fields = ('player__name', 'achievement')
    ordering = ('player',)
