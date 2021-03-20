# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'icon2x', 'description')
    list_filter = ()
    search_fields = ('title', 'description')
    ordering = ('title',)


@admin.register(models.PlayerBadge)
class PlayerBadgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'badge', 'granted_at')
    list_filter = ('badge',)
    search_fields = ('player__name', 'badge__title')
    ordering = ('id',)


'''
@admin.register(models.GuildBadge)
class GuildBadgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'guild', 'type', 'acquired_at')
    list_filter = ()
    search_fields = ('guild__name', 'type__title')
    ordering = ('id',)
'''
