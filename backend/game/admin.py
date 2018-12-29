# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'flags', 'started_at', 'duration')
    list_filter = ('type',)
    search_fields = ('name',)
    filter_horizontal = ('players', 'winners')
    ordering = ('-id',)


@admin.register(models.GameReward)
class GameRewardAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'type', 'amount')
    list_filter = ('type',)
    search_fields = ()
    ordering = ('-id',)


@admin.register(models.GameArchive)
class GameArchiveAdmin(admin.ModelAdmin):
    list_display = ('game',)
    list_filter = ()
    search_fields = ()
    ordering = ('-game__id',)

# Register your models here.
